from pydantic import BaseModel, Field
import logging
import anthropic
from app.core.config import get_settings
import time


class StructuredFields(BaseModel):
    # normal Pydantic model
    context: str | None = Field(
        default=None,
        description="Background/situation the note is set in, if the note gives any",
    )
    problem: str | None = Field(
        default=None,
        description="The problem or question being addressed, if the note describes one",
    )
    investigation: str | None = Field(
        default=None,
        description="What was tried or explored to understand/solve it, if the note mentions any",
    )
    fix: str | None = Field(
        default=None,
        description="The resolution or solution applied, if the note describes one",
    )
    takeaway: str | None = Field(
        default=None,
        description="The generalizable lesson or insight, if the note has one",
    )


logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You extract structure from a developer's raw journal note. Entry types "
    "mean: note (general observation), decision (a choice made and why), "
    "bug (a problem hit and how it was diagnosed/fixed), milestone (something "
    "shipped/completed), learning (something newly understood), question "
    "(something open/unresolved).\n\n"
    "Fill in only the fields the note's type and content actually support; "
    "leave a field null rather than guessing or padding it out — a short "
    "note may only support one or two fields, and that is expected, not an "
    "error. Keep each field terse and grounded in the note's own words; do "
    "not invent detail, backstory, or elaboration the note doesn't contain."
)

_MODEL = "claude-sonnet-5"


def structure_note(raw_note: str, entry_type: str) -> StructuredFields | None:
    # builds a client using the key from my .env
    client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key or None)

    start = time.perf_counter()
    try:
        response = client.messages.parse(
            model=_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Entry type: {entry_type}\n\nRaw note:\n{raw_note}",
                }
            ],
            output_format=StructuredFields,
        )
        duration = time.perf_counter() - start
        logger.info("Claude structuring ok model=%s duration=%.2fs", _MODEL, duration)
        return response.parsed_output

    except anthropic.APIError as e:
        duration = time.perf_counter() - start
        logger.warning(
            "Claude structuring failed model=%s duration=%.2fs error=%s", _MODEL, duration, e
        )
        return None


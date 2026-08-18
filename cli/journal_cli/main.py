# the actual journal_log command

import httpx
import typer

from journal_cli import client
from journal_cli.config import get_settings
from journal_cli.git_utils import detect_project

app = typer.Typer()


@app.callback()
def callback() -> None:
    """dev-journal CLI."""


#  registers 'log' as a subcommand. call it as journal log "some note"
@app.command()
def log(
    note: str,
    # typer.Option(None...) makes --project an optional named flag rather than an argument;
    # the help= text shows up automatically in journal log --help, for free.
    project: str | None = typer.Option(None, "--project", help="Override auto-detected project"),
    entry_type: str = typer.Option(
        "note", "--type", help="note/decision/bug/milestone/learning/question"
    ),
) -> None:
    resolved_project = detect_project(project)

    try:
        entry = client.create_entry(raw_note=note, project=resolved_project, entry_type=entry_type)
    except httpx.ConnectError:
        # httpx.ConnectError means "couldn't even reach the server" (backend not running)
        typer.secho(
            f"Could not reach the backend at {get_settings().api_url} — is it running?",
            fg=typer.colors.RED,
        )
        # clean error message and non-zero exit, not a stack trace
        raise typer.Exit(code=1) from None

    typer.secho(
        f"Logged entry #{entry['id']} to project '{resolved_project}'", fg=typer.colors.GREEN
    )


if __name__ == "__main__":
    app()

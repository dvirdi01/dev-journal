import httpx

from journal_cli.config import get_settings

def create_entry(raw_note: str, project: str, entry_type: str = "note") -> dict:
    settings = get_settings()
    # makes a real network call 
    response = httpx.post(
        # builds the full URL from your configurable api_url
        # this is the one place the CLI actually knows where your backend lives.
        f"{settings.api_url}/entries",
        json={"raw_note": raw_note, "project": project, "entry_type": entry_type},
    )
    #  if the backend returns an error status (4xx/5xx), this raises an 
    # exception immediately instead of silently returning bad data.
    response.raise_for_status()
    # the created entry as a plain dict, which main.py will use to 
    # print a confirmation.
    return response.json()
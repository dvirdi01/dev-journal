import logging

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

# configures python's built-in logging module to log messages (e.g., INFO, DEBUG, ERROR).
logging.basicConfig(level=settings.log_level)
# call this instead of print(...) to log messages.
logger = logging.getLogger(__name__)

# app object: uvicorn will look for this object to run the FastAPI application.
app = FastAPI(title="dev-journal", version="0.1.0")


# Registers a function as a route handler for the GET method at the root URL ("/").
@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

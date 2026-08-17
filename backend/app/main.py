import logging
from fastapi import FastAPI
from app.core.config import get_settings

settings = get_settings()

# configures python's built-in logging module to log messages at the level specified in the settings (e.g., INFO, DEBUG, ERROR). This ensures that log messages are output according to the desired verbosity level, which can be useful for debugging and monitoring the application.
logging.basicConfig(level=settings.log_level)
# call this instead of print(...) to log messages. The logger is named after the module's name (__name__), which helps identify where the log messages are coming from when reviewing logs.
logger=logging.getLogger(__name__)

# app object: uvicorn (the ASGI server) will look for this object to run the FastAPI application. The title and version parameters are used for documentation purposes, such as in the automatically generated OpenAPI docs. It is the object every router gets attached to later.
app = FastAPI(title="dev-journal", version="0.1.0")

# a decorator that registers a function as a route handler for the GET method at the root URL ("/"). When a GET request is made to the root URL, this function will be called, and it returns a simple JSON response indicating that the application is running.
@app.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint to verify that the application is running.
    Returns a simple JSON response indicating the health status.
    """
    return {"status": "healthy"}
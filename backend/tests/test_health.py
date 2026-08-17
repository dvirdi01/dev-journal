from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings

# wraps my FastAPI app in a test client that can be used to simulate requests to the application without running a live server. This allows for testing the endpoints and their responses in an isolated environment.
client = TestClient(app)

def test_health():
    # Arrange: (nothing needed here, client already exists at module level)
    # Act: do the thing you're testing
    response = client.get("/health")
    # Assert: check it did what you expected
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# testing for non-existing routes 
def test_nonexistent_route_returns_404():
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404

# testing something that isnt an HTTP endpoint
def test_settings_defaults():
    settings = Settings(_env_file=None)  # ignore .env, test pure defaults
    assert settings.database_url == "sqlite:///./dev_journal.db"
    assert settings.log_level == "INFO"
    assert settings.anthropic_api_key is None
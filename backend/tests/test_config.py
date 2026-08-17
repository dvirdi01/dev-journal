from app.core.config import Settings

# simulates requests to the application without running a live server.


# testing something that isnt an HTTP endpoint
def test_settings_defaults():
    settings = Settings(_env_file=None)  # ignore .env, test pure defaults
    assert settings.database_url == "sqlite:///./dev_journal.db"
    assert settings.log_level == "INFO"
    assert settings.anthropic_api_key is None

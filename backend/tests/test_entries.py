import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


# any test that takes client as a param automatically
# gets whatever this fixture yields.
@pytest.fixture
def client():
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # allows multiple connections to the same in-memory db
    )
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Dependency override to use the test database
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()  # Clear overrides after the test


def test_create_entry(client):
    response = client.post("/entries", json={"raw_note": "Test note", "project": "EchoPrep"})
    assert response.status_code == 201
    data = response.json()
    assert data["raw_note"] == "Test note"
    assert data["entry_type"] == "note"
    assert data["project"] == "EchoPrep"
    assert data["id"] is not None


def test_list_entries_filters_by_project(client):
    # Create entries for different projects
    client.post("/entries", json={"raw_note": "Note A", "project": "EchoPrep"})
    client.post("/entries", json={"raw_note": "Note B", "project": "dev-journal"})

    # List entries filtered by project
    response = client.get("/entries", params={"project": "EchoPrep"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["raw_note"] == "Note A"

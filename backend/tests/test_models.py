from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.entry import Entry


def test_entry_round_trip():
    engine = create_engine("sqlite:///:memory:")  # temp db that is deleted once connection closes
    # creates tables directly from your model definition
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    entry = Entry(raw_note="hit a bug in auth", project="EchoPrep", entry_type="bug")
    session.add(entry)
    session.commit()

    saved = session.query(Entry).filter_by(project="EchoPrep").one()
    assert saved.raw_note == "hit a bug in auth"
    assert saved.entry_type == "bug"
    assert saved.id is not None
    assert saved.created_at is not None

    session.close()

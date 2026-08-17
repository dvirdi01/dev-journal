from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# the connection to my SQLite file  is established here.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# tracks objects I have loaded/changed until I commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# SQLAlchemy uses this base class to keep track of all the models and their relationships
class Base(DeclarativeBase):
    pass


# A generator used with FastAPI's Depends(). FastAPI calls it per-request
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

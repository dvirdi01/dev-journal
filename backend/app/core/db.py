from collections.abc import Generator
from sqlalchemy import create_engine    
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import get_settings

settings = get_settings()

# the connection to my SQLite file (dev_journal.db) is established here. The connect_args={"check_same_thread": False} argument is specific to SQLite and allows the connection to be shared across different threads, which is necessary for web applications that handle multiple requests concurrently.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# A factory for database sessions (a session is a conversation with the DB)- It tracks objects I have loaded/changed until I commit. Autocommit=False means I have to explicitly commit changes to the DB, and autoflush=False means changes are not automatically sent to the DB until I commit. The bind=engine argument associates this session factory with the engine we created earlier, so that sessions created by this factory will use that engine to connect to the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every table model will inherit from this. SQLAlchemy uses this base class to keep track of all the models and their relationships, allowing it to generate the appropriate SQL statements for creating tables, inserting data, querying, etc.
class Base(DeclarativeBase):
    pass

# A generator used with FastAPI's Depends(). FastAPI calls it per-request, yielding a database session that can be used in the request handler. After the request is done, it ensures that the session is closed, preventing resource leaks and ensuring that connections are returned to the pool.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
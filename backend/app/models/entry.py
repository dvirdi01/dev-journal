# Defines a jounral entry model for the database.

from datetime import datetime

from sqlalchemy import JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


# Mapped[int] means that the id attribute is mapped to a database column of type integer.
# It is sqlalchemy 2.0's types style
# str | None means nullable, str means NOT NULL
class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)  # mas id as primary key
    raw_note: Mapped[str]
    entry_type: Mapped[str] = mapped_column(default="note")
    context: Mapped[str | None] = mapped_column(default=None)
    problem: Mapped[str | None] = mapped_column(default=None)
    investigation: Mapped[str | None] = mapped_column(default=None)
    fix: Mapped[str | None] = mapped_column(default=None)
    takeaway: Mapped[str | None] = mapped_column(default=None)
    project: Mapped[str] = mapped_column(index=True)  # tells db to build a lookup index on this col
    # so WHERE project='EchoPrep', queries stay fast
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

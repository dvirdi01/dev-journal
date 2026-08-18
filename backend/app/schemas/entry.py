from datetime import datetime
from pydantic import BaseModel, ConfigDict

# decoupling this from entry model means we can change 
# our DB schema without automatically changing our API contract 


# this is what a client sends in
# rest gets filled in later with claude 
class EntryCreate(BaseModel):
    raw_note: str
    project: str 
    tags: list[str] | None = None

# what goe s out 
class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # tells pydantic to read from the SQLAlchemy model attributes

    id: int
    raw_note: str
    context: str | None = None
    problem: str | None = None
    investigation: str | None = None
    fix: str | None = None
    takeaway: str | None = None
    project: str
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime
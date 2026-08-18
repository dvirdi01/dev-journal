from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.entry import EntryCreate, EntryRead
from app.services import entries as entries_service

# mini FastAPI a[[ where we define routes on
router = APIRouter()


# Depends(get_db) tells FastAPI to call get_db and pass the result into the db parameter
@router.post("", response_model=EntryRead, status_code=201)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)):
    return entries_service.create_entry(db, payload)


@router.get("", response_model=list[EntryRead])
def list_entries(project: str | None = None, db: Session = Depends(get_db)):
    return entries_service.list_entries(db, project)


@router.get("/{entry_id}", response_model=EntryRead)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = entries_service.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

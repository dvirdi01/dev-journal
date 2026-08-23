from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.entry import Entry
from app.schemas.entry import EntryCreate
from app.services.claude_structuring import structure_note

def create_entry(db: Session, payload: EntryCreate) -> Entry:
    # converts pydantic object into plain dict
    entry = Entry(**payload.model_dump())

    structured = structure_note(payload.raw_note, payload.entry_type)
    if structured is not None:
        entry.context = structured.context
        entry.problem = structured.problem
        entry.investigation = structured.investigation
        entry.fix = structured.fix
        entry.takeaway = structured.takeaway
        
    db.add(entry)
    db.commit()  # saves the row
    db.refresh(entry)  # re-reads the row from the db
    return entry


def list_entries(db: Session, project: str | None = None) -> list[Entry]:
    query = db.query(Entry)
    if project:
        query = query.filter(Entry.project == project)
    return query.order_by(Entry.created_at.desc()).all()


def get_entry(db: Session, entry_id: int) -> Entry | None:
    return db.get(Entry, entry_id)

def search_entries(db: Session, q: str, project: str | None = None) -> list[Entry]:
    sql = "SELECT entries.* FROM entries JOIN entries_fts ON entries.id = entries_fts.rowid WHERE entries_fts MATCH :q"
    params = {"q": q}
    if project:
        sql += " AND entries.project = :project"
        params["project"] = project
    sql += " ORDER BY bm25(entries_fts)"

    rows = db.execute(text(sql), params).mappings().all()
    return [db.get(Entry, row["id"]) for row in rows]

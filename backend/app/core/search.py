FTS_SETUP_SQL = [
    """
    CREATE VIRTUAL TABLE entries_fts USING fts5(
        raw_note, context, problem, investigation, fix, takeaway,
        content='entries',
        content_rowid='id'
    )
    """,
    """
    CREATE TRIGGER entries_ai AFTER INSERT ON entries BEGIN
        INSERT INTO entries_fts(rowid, raw_note, context, problem, investigation, fix, takeaway)
        VALUES (new.id, new.raw_note, new.context, new.problem, new.investigation, new.fix, new.takeaway);
    END
    """,
    """
    CREATE TRIGGER entries_ad AFTER DELETE ON entries BEGIN
        INSERT INTO entries_fts(entries_fts, rowid, raw_note, context, problem, investigation, fix, takeaway)
        VALUES ('delete', old.id, old.raw_note, old.context, old.problem, old.investigation, old.fix, old.takeaway);
    END
    """,
    """
    CREATE TRIGGER entries_au AFTER UPDATE ON entries BEGIN
        INSERT INTO entries_fts(entries_fts, rowid, raw_note, context, problem, investigation, fix, takeaway)
        VALUES ('delete', old.id, old.raw_note, old.context, old.problem, old.investigation, old.fix, old.takeaway);
        INSERT INTO entries_fts(rowid, raw_note, context, problem, investigation, fix, takeaway)
        VALUES (new.id, new.raw_note, new.context, new.problem, new.investigation, new.fix, new.takeaway);
    END
    """,
]

FTS_TEARDOWN_SQL = [
    "DROP TRIGGER IF EXISTS entries_au",
    "DROP TRIGGER IF EXISTS entries_ad",
    "DROP TRIGGER IF EXISTS entries_ai",
    "DROP TABLE IF EXISTS entries_fts",
]
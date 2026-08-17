# dev-journal — Project Context

Source of truth for this project's architecture, decisions, errors, and
learnings lives in Notion, not in this repo:

**Dev Journal / Build Log — Project History & Decision Log**
https://app.notion.com/p/3bef6396b7ef8152bbb9c0ceafcc97b8

## Logging rule

Any of the following happening during a session in this repo should be
logged as an entry in that Notion page (not just left in chat scrollback
or commit messages):

- Architectural decisions (what was chosen, what was rejected, why)
- Errors/bugs hit and how they were diagnosed or fixed
- Progress/milestones (what got built, in what order)
- Learnings (anything that would change how you'd approach it next time)
- Open questions / things deferred to later

Before starting non-trivial work, check the Notion page for current
state and prior decisions. After finishing a step, log what happened —
this is what feeds the eventual LinkedIn Content Assistant project, so
entries should be real, not placeholder text.

## Snapshot (may drift — Notion is authoritative)

This project is itself the subject of the Dev Journal: an AI-powered
developer journal with retrieval-based search for logging debugging
sessions, blockers, and decisions, then querying them in natural language.

**Stack (v1, deliberately downscoped from an earlier Postgres+Docker plan):**
- DB: SQLite (FTS5 for keyword search now; `sqlite-vec` or embeddings later if needed)
- Backend: FastAPI
- ORM/migrations: SQLAlchemy + Alembic
- Frontend: Streamlit
- LLM: Claude API (structuring notes + answering queries)
- Embeddings: undecided — Voyage AI, or skip for v1 and rely on FTS5
- CLI: Typer (`journal log "..."`)

**Guiding principle:** match infra complexity to what's actually being
learned at each stage — don't stack containers/networking/pooling/vector-DB
concepts before one working endpoint exists.

**Intended folder structure** (see Notion page for current actual state):
```
dev-journal/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   └── requirements.txt
├── cli/
│   └── journal_cli.py
├── frontend/
│   └── app.py
└── .env
```

For full detail — the RAG-scope reasoning, phase-by-phase roadmap, and
the running Progress/Learnings logs — read the Notion page directly.

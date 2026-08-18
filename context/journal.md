# Dev Journal — Build Log

Source of truth for this project's architecture, decisions, errors, and
learnings. Feeds the future LinkedIn Content Assistant project, so entries
should be real, not placeholder text.

**Format going forward:** append a new entry under "Session Log" per
session with non-trivial work — decision, error/fix, milestone, learning,
or open question. Structure each as Context → Problem/Decision →
Investigation → Fix/Outcome → Takeaway (skip fields that don't apply).
Newest entries go at the bottom.

---

## Imported from Notion (2026-08-16)

The dev-journal project's own build log lived in Notion up to this point
(migrated 2026-08-16 — see CLAUDE.md for why). Preserved verbatim below.

### Overview

This is the first project in the 4-week Marathon Plan (see Future Project
Ideas). Goal: log milestones, blockers, roadmaps, and decisions while
building, to fuel LinkedIn posts later. Meta-twist: using the Dev
Journal's own structure to log the Dev Journal's own build.

### Why This Project First

- Tagged Priority 1 in Future Project Ideas — simplest, no dependencies, builds momentum
- Feeds the LinkedIn Content Assistant (project #4), which needs real Dev Journal entries to work from, not fake test data

### Key Decision: Build a Real App, Not a Skill or Markdown File

**Question raised:** Could this just be a markdown file Claude reads and summarizes, or a Claude skill?

**Answer worked through:** For personal scale (a few hundred entries), yes
— a markdown/JSON file fed to Claude on query is a completely legitimate,
simpler v1. Over-engineering RAG for a dataset that doesn't need it would
actually read badly to a technical audience.

**Decision:** Build it as a real application anyway — specifically because:
1. Don't want it to be something replicable with one built-in Claude command
2. Want persistent, queryable storage that scales without re-uploading/re-processing everything each time
3. Want passive/terminal capture (CLI, git hooks) — not just something invoked inside a Claude chat
4. Want a real UI (Streamlit) — something demoable/screen-recordable for LinkedIn, not just chat output
5. Want structured analytics (e.g., time spent per project) — real SQL aggregation, not something a chat skill produces

### Where RAG Actually Belongs (Important Correction)

Initial framing overstated RAG's role — it isn't really involved in most
flows. Corrected understanding:
- **Flow: "summarize my week"** → date/tag filtering, not semantic search
- **Flow: "give me LinkedIn content"** → tag filtering (generalizable lesson vs one-off)
- **Flow: "have I seen this before"** → this is the ONE flow that's genuinely RAG — semantic similarity search across potentially hundreds of entries

**Honest technical narrative decided on:** "Started simple (full-context),
hit a real scaling wall as entries grew, added retrieval to fix it" — not
"used RAG because it sounds impressive." RAG's real value proposition here
is token efficiency: at 50 entries context-stuffing is fine; at 2,000
entries it's the difference between ~200 tokens and ~100,000 tokens per
query.

### User Flows (as understood/confirmed)

1. **Capture** — while working (e.g. on Voltra), invoke via hotkey/CLI (`journal log`) or write a rough note; Claude structures it into Context → Problem → Investigation → Fix → Takeaway and saves + embeds it immediately
2. **Weekly summary query** — "summarize what I worked on this week" → date-filtered retrieval → Claude drafts a clean summary grouped by project/status
3. **"Have I seen this before" query** — mid-debug, semantic search across all past entries regardless of date/project → Claude surfaces the closest past incident and its fix
4. **LinkedIn content query** — pull tag-filtered "generalizable lesson" entries from a date range → Claude drafts 2-3 post angle options, user edits/approves (no auto-posting)

### Chosen Tech Stack (original, with rationale)

- **Database:** PostgreSQL + pgvector extension (via Docker) — one database instead of running a separate dedicated vector DB (Pinecone/Weaviate); sufficient and simpler at personal scale
- **Backend:** FastAPI — clean separation of API routes, business logic (services), and data models
- **Frontend:** Streamlit — fast to build, good enough to demo/screen-record
- **Embeddings:** OpenAI embeddings API
- **LLM (structuring + query answering):** Claude API
- **CLI:** Typer-based Python CLI for `journal log` callable from anywhere in terminal
- **Migrations:** Alembic — version-controlled schema evolution instead of hand-editing tables

### Tech Stack Revision (after further review)

Original Postgres+Docker+pgvector stack reconsidered as over-engineered
for a v1 learning project. Revised:

- **Database:** SQLite for v1 (zero setup, single file) instead of Postgres+Docker — avoids stacking containers/networking/pooling before writing any app logic. Use SQLite FTS5 (keyword/BM25 search) as a zero-infra stand-in for "have I seen this before," or `sqlite-vec` if going straight to embeddings. Migrate to Postgres+pgvector later when there's a real reason (multi-user, deployment) — that migration becomes its own story.
- **Backend:** FastAPI — kept.
- **ORM:** SQLAlchemy + Alembic — kept, don't over-invest in migrations early.
- **Frontend:** Streamlit — kept for v1; known ceiling around chat UX (full script rerun per interaction) — switching to a real frontend later is a legitimate v2 story.
- **Embeddings:** reconsider OpenAI-only (extra provider/bill for one function). Options: Voyage AI (Anthropic's recommended embedding partner), or skip embeddings for v1 and rely on FTS5 keyword search, upgrading only if keyword search demonstrably misses things.
- **LLM:** Claude API — kept.
- **CLI:** Typer — kept.

**Guiding principle:** match infra complexity to what's actually being
learned at each stage — don't stack 5 new concepts (containers,
networking, Postgres, pgvector, pooling) before shipping one working
endpoint.

### Folder Structure Decided

```
dev-journal/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers (entries.py, query.py)
│   │   ├── core/              # config.py, db.py
│   │   ├── models/            # SQLAlchemy models (entry.py)
│   │   ├── services/          # embeddings.py, structuring.py, retrieval.py
│   │   └── main.py            # FastAPI entrypoint
│   ├── alembic/                # DB migrations
│   └── requirements.txt
├── cli/
│   └── journal_cli.py
├── frontend/
│   └── app.py                  # Streamlit chat/dashboard
├── docker-compose.yml
└── .env
```

### Learning Roadmap (Phases)

**Phase 0 — Framing decisions** (see above: why build vs skill/markdown, where RAG belongs)

**Phase 1 — Environment & Data Layer**
1. Init git repo + folder skeleton
2. Docker + Docker Compose → run Postgres with pgvector locally
3. Understand Postgres+pgvector vs dedicated vector DB tradeoff

**Phase 2 — Schema & ORM**
1. SQLAlchemy models — Entry table (context, problem, investigation, fix, takeaway, project, tags, embedding vector, timestamps)
2. Alembic migrations

**Phase 3 — Backend API**
1. FastAPI skeleton — first working endpoint (POST /entries)
2. Embeddings service — OpenAI embeddings call + vector storage
3. Claude API integration — raw note → structured entry; also powers query/chat endpoint
4. Retrieval logic — cosine similarity search (GET /query) + plain filtered queries

**Phase 4 — Interfaces**
1. CLI tool (Typer) — `journal log "..."`. Must support cross-repo use as
   a first-class feature, not an afterthought: auto-detect the calling
   project (git remote/repo name of the cwd) with a `--project` override,
   since the intended usage is running `journal log` from inside *other*
   codebases (e.g. Volentia), not just from within dev-journal itself.
2. Streamlit frontend — chat interface + basic dashboard (e.g. time per project)

**Phase 5 — The scaling wall story**
1. Once real entries accumulate, deliberately measure/document context-stuffing cost vs. retrieval cost — this comparison is the actual LinkedIn post

### Progress Log

**Step 1 — Repo Initialized**

Commands run to scaffold the repo:
```bash
mkdir dev-journal && cd dev-journal
git init
mkdir -p backend/app/api backend/app/core backend/app/models backend/app/services backend/alembic cli frontend
touch backend/requirements.txt backend/app/main.py docker-compose.yml .env .gitignore
```

`.gitignore` contents:
```
__pycache__/
*.pyc
.env
venv/
.DS_Store
```

**Rationale:** Empty skeleton with the right folders forces separation of
concerns (API vs business logic vs data models) before writing app code —
the difference between "production-style" and "one big script."

**Next up (as of import):** Step 2 — docker-compose.yml to spin up
Postgres + pgvector. Note: superseded by the SQLite-first revision above —
Phase 1 should start from the SQLite plan, not this original Docker step.

### Learnings Log

- Learned how to initialize a GitHub repo (README, .gitignore, license) and clone it locally as the starting point for a project
- Learned how to give a repo persistent context for AI coding agents: add a `CLAUDE.md` at the repo root describing architecture/decisions/roadmap, then a thin `AGENTS.md` that just points to it (`AGENTS.md` is the filename other tools like Codex/Cursor look for, so this makes the same context portable across tools instead of duplicating it). *(Superseded 2026-08-16 — see below: journal moved from Notion into this file.)*

### 2026-08-16 — Reality check: what is this project actually for

**Context:** Got confused partway through setup about whether dev-journal
was worth building, since the stated need ("easily track my comments,
questions, workflow, decisions") was already fully solved by
`context/journal.md` itself — no app required.

**Decision:** Keep building the app anyway, but on the honest motivation:
learning (hands-on FastAPI/SQLite/retrieval practice) and a portfolio
piece — not because tracking-my-work requires it. The earlier "why build
a real app, not a markdown file" reasoning (see above) was framed as
product logic; that's still true but wasn't the real driver.

**Takeaway:** separating "the need" (tracking — already solved, free)
from "the reason to build" (learning + portfolio) should shape scoping
going forward — invest effort in the parts that teach something or demo
well (retrieval, structured queries, a real UI), and keep the rest as
thin as possible rather than gold-plating plumbing no one will see.

### 2026-08-16 — Learning: requirements.txt and `__init__.py` basics

**Context:** First time setting up a Python backend from scratch (Phase 1,
dependencies + config step) — both of these were new.

**Learning — `requirements.txt`:** a plain text file listing the
packages a project depends on (one per line, e.g. `fastapi`,
`sqlalchemy>=2.0`), installed all at once with
`pip install -r requirements.txt`. Split into two files here:
`requirements.txt` (what the app needs to actually run — fastapi,
uvicorn, sqlalchemy, alembic, pydantic-settings, anthropic, httpx) vs
`requirements-dev.txt` (what only the developer needs — pytest, ruff).
The split matters because a deployed server never needs a test runner or
linter installed.

**Learning — `__init__.py`:** an empty file placed in a folder to mark it
as a Python *package*, which is what makes `from backend.app.core.config
import get_settings`-style imports work across nested folders
(`backend/app/__init__.py`, `backend/app/core/__init__.py`). Without it,
Python may not reliably treat the folder as something importable — hit
this directly when the first import attempt needed both files to exist
before it worked.

**Takeaway:** these are two of the "invisible scaffolding" pieces that
tutorials often skip because they assume it — worth remembering neither
was obvious coming in fresh.

### 2026-08-16 — Bug: `db.py` import failed depending on working directory

**Problem:** `python -c "from backend.app.core.db import engine, Base; ..."`
run from the repo root raised `ImportError: cannot import name 'engine'
from 'backend.app.core.db'` — despite `engine` clearly being defined in
the file.

**Investigation:** `db.py` internally does `from app.core.config import
get_settings`, which assumes `app` is directly importable — true only
when the working directory is `backend/` (matching how the app is meant
to actually run: `uvicorn app.main:app --reload` from inside `backend/`).
The Step 2 test command for `config.py` had instead been run from the
repo root using a `backend.app.core...` prefix — that happened to work
for `config.py` alone (no internal `app.xxx` imports) but silently broke
for `db.py`, which does import that way internally.

**Fix:** `cd backend` before running any ad-hoc import tests, matching
the working directory the real server will run from.

**Takeaway:** when a Python project's "run from here" directory matters
(as it does whenever internal imports use a package-relative style like
`app.xxx` instead of `backend.app.xxx`), ad-hoc test commands need to
match that same working directory — testing from a different cwd than
production can produce confusing, inconsistent import errors that look
like a code bug but are actually a working-directory mismatch.

### 2026-08-16 — Learning: `ruff check` vs `ruff format`, and a comment-trimming gotcha

**Context:** Closing out Phase 1 by adding ruff lint/format config and
running it for the first time.

**Learning — two separate ruff commands, not one:** `ruff check .`
*lints* (finds unused imports, unsorted imports, undefined names, style
violations) and only it accepts `--fix` to auto-correct what it safely
can. `ruff format .` *reformats* code style (whitespace, quote style,
line wrapping) and needs no `--fix` flag — formatting the file *is* the
fix; running `ruff format . --fix` errors because `--fix` isn't a valid
argument for that subcommand.

**Bug hit — deleting code while trimming a comment:** while shortening
the long tutorial-style comments in `main.py` down to one-liners (per
ruff's `E501` line-too-long complaints), the actual code lines sitting
next to two comments (`logger = logging.getLogger(__name__)` and
`app = FastAPI(...)`) got deleted along with the comment text, not just
the comment. Result: `F821 Undefined name 'app'` from ruff, and it would
have been a runtime `NameError` too — the `@app.get("/health")`
decorator had nothing to attach to.

**Fix:** restored the two code lines; rule going forward — when trimming
a comment, only delete the `#` line itself, never touch the code line
beside it.

**Takeaway:** the underlying lesson (why the comments were too long in
the first place) is a professional-code habit worth keeping: comments
should capture the "why," not the "what" — verbose paragraph explanations
belong in a journal/commit message/PR description, not inline, both
because they go stale and because they trip line-length linting.

### 2026-08-17 — Learning: SQLAlchemy models + Pydantic schemas for building database entries

**Context:** Phase 2, Steps 1-2 — first real database table (`Entry`) and
its API request/response contracts.

**Learning — SQLAlchemy 2.0 typed models:** `Mapped[str]` vs
`Mapped[str | None]` in a type annotation is what tells SQLAlchemy
`NOT NULL` vs nullable, and gives real editor autocomplete/type-checking
in the process. `mapped_column()` is only needed when there's something
to configure beyond the type — `primary_key=True` marks the ID column,
`index=True` builds a DB-level lookup index (needed on `project` since
that's what gets filtered on), `JSON` stores a Python list as encoded
text (chosen over a separate tags table — simpler at this scale, no
joins). `server_default=func.now()` is different from a plain Python
`default=`: the former makes the *database* fill in the timestamp on
insert (works even if some other tool writes to the table, bypassing
Python entirely); `onupdate=func.now()` refreshes a column automatically
on every update.

**Learning — separate Pydantic schemas from the DB model:**
`EntryCreate` (what a client sends in) and `EntryRead` (what the API
sends back) are deliberately different, smaller classes than the full
`Entry` table — not a straight reuse of the model. `EntryCreate` only
asks for `raw_note`/`project`/`tags`, since the structured fields get
filled in later by Claude, not by whoever's logging the note.
`EntryRead` needs `model_config = ConfigDict(from_attributes=True)` to
be built directly from a SQLAlchemy object's attributes instead of only
from a plain dict.

**Decision:** made `project` required (not nullable) in `EntryCreate`,
diverging slightly from the original rough plan — since the DB column is
`NOT NULL`, letting `None` through would surface as an ugly database
error instead of FastAPI's clean 422 validation response.

**Takeaway:** decoupling the API shape from the DB shape means the
schema can evolve independently — e.g. an internal-only column added to
`Entry` later won't leak over the API unless deliberately added to
`EntryRead` too.

### 2026-08-17 — Learning: Alembic upgrade/downgrade terminology, and peeking inside SQLite directly

**Context:** Ran the first real migration (`alembic upgrade head`) and
got confused about what "upgrade" and "entries table" actually meant.

**Learning — "upgrade" is a schema operation, not a data operation:**
Alembic's `upgrade`/`downgrade` change the *structure* of the database
(create/drop tables, add/remove columns) — never rows of data. "create
entries table" means the table named `entries` now exists; it says
nothing about whether any journal entries (rows) exist inside it. Ran
`alembic downgrade base` then `alembic upgrade head` back-to-back as a
round-trip check — both directions worked cleanly.

**Learning — where the database actually lives and how to look inside
it:** SQLite has no server process; `dev_journal.db` is just a single
file at `backend/dev_journal.db`, created the moment the first migration
ran (didn't exist before). Peeked inside it directly with Python's
built-in `sqlite3` module (no extra install needed):
```python
import sqlite3
conn = sqlite3.connect("dev_journal.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")  # list tables
cur.execute("PRAGMA table_info(entries)")  # columns: cid, name, type, notnull, default, is_pk
cur.execute("SELECT * FROM alembic_version")  # confirms which migration is currently applied
```
Confirmed: `entries` table has 0 rows (empty, as expected — nothing
inserts data until Phase 3's API exists), and `alembic_version` holds
exactly one row containing the migration ID `c15bab78e938`, which is the
actual mechanism behind "Alembic knows what's been applied."

**Bug caught along the way:** `dev_journal.db` wasn't in `.gitignore` —
would have been committed to git on the next broad `git add`, and it'll
eventually hold real personal journal entries that shouldn't be in
version-control history. Added `*.db` and `*.db-journal` to
`.gitignore` before this went any further.

**Takeaway:** when a concept feels abstract (like "what does upgrading a
schema even mean"), inspecting the raw artifact directly — here, just
querying the SQLite file with stdlib `sqlite3` — collapses the
abstraction fast and confirms the model/migration actually did what was
intended.

### 2026-08-17 — Learnings: service layer, FastAPI router, and a trailing-slash gotcha

**Context:** Phase 3A — building `services/entries.py` and
`api/entries.py`, the first endpoints that actually let entries be
created/read over HTTP.

**Bug hit — parameter/variable name mismatch caused a `NameError`:**
`create_entry`'s parameter was named `entry` but the function body
referenced `payload.model_dump()` — `payload` didn't exist, so calling it
would have raised `NameError` at runtime. Even past the typo, reusing the
same name (`entry`) for both the incoming `EntryCreate` and the resulting
`Entry` ORM object would have been confusing to read. Fixed by naming the
parameter `payload` throughout.

**Design decision — `entry_type` should have a default, not be
required:** `EntryCreate.entry_type` was briefly made required (no
default), which would have forced every future `journal log` call to
specify a type explicitly. Reverted to `entry_type: str = "note"` — most
day-to-day logging is quick and uncategorized; explicit tagging
(decision/bug/milestone/etc.) should be an opt-in override, not mandatory
friction on the common case.

**Learning — FastAPI dependency injection (`Depends`):** `Depends(get_db)`
tells FastAPI to call `get_db()` before running the endpoint, hand the
yielded session to the function, and clean it up after — automatically,
per request. Removes the need to manually open/close a DB session inside
every route.

**Learning — `response_model` is separate from the function's actual
return type:** route functions return raw SQLAlchemy `Entry` objects;
`response_model=EntryRead` controls how FastAPI serializes that into
JSON (via `EntryRead`'s `from_attributes`) and strips anything not
defined on the schema — so a field could never accidentally leak over
the API just because it exists on the DB model.

**Learning — `""` vs `"/"` on a mounted router, and the 307-redirect
gotcha:** with `router = APIRouter()` mounted via
`app.include_router(entries.router, prefix="/entries")`, defining a route
as `"/"` makes the real path `/entries/` — and FastAPI silently issues a
307 redirect from `/entries` (no trailing slash) to `/entries/` to fix
the mismatch. That's invisible in a browser but breaks CLI/HTTP clients
that don't follow redirects by default. Using `""` instead of `"/"` for
the router's base routes avoids the redirect entirely, since the real
path becomes exactly `/entries`.

**Takeaway:** the trailing-slash behavior is exactly the kind of subtle
framework default that only surfaces once something calls the API
non-interactively (like the future CLI) — worth remembering as a class
of bug to watch for: things that "just work" in a browser can silently
break for a script.

### 2026-08-17 — Milestone: first entry created and retrieved over real HTTP

**What happened:** `POST /entries` and `GET /entries` both work end to
end for the first time — `curl` a raw note in, get back a fully
persisted, structured row (auto-assigned `id`, `entry_type` defaulting
to `"note"`, real timestamps), then `GET /entries` returns it in a JSON
array straight from `dev_journal.db`.

**Why this is the real milestone (not the migration, not the model):**
this is the concrete thing that was actually promised back when deciding
to build a real app instead of a markdown file — persistent, queryable
storage reachable over HTTP, not something a flat file or a Claude skill
could produce. Phase 3A is functionally done: create + list + get all
work.

**Takeaway:** everything before this (config, DB session, model, Alembic,
service layer, router) was infrastructure in service of this one moment
— worth remembering when the next phase's setup feels like "more
plumbing before anything real happens" again.

### 2026-08-17 — Learnings: ruff's B008 false positive on `Depends`, and a TOML table-ordering bug

**Context:** Closing out Phase 3A — running `ruff check .` on the new
router.

**Learning — `B008` flags `Depends(...)` as the mutable-default-argument
bug, but it isn't one:** `B008` (flake8-bugbear) normally protects
against a real Python gotcha — default argument values are evaluated
*once*, at function-definition time, not per call (the classic `def
f(x=[])` trap). `Depends(get_db)` looks like that pattern but isn't:
FastAPI inspects the function signature itself and calls `get_db()`
fresh on every request — it's the intended, idiomatic way to write
FastAPI routes, used throughout FastAPI's own docs. Fixed by telling
ruff to treat it as safe rather than suppressing the warning line by
line:
```toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["fastapi.Depends", "fastapi.Query", "fastapi.Path"]
```

**Bug hit — TOML table headers aren't nesting brackets:** adding the
section above (placed *before* the existing `select = [...]` line, with
no explicit `[tool.ruff.lint]` header of its own) broke parsing:
`unknown field 'select', expected 'extend-immutable-calls'`. In TOML,
every key after a `[table.header]` belongs to that table until the next
header appears, regardless of indentation — so `select` was being read
as a field of `flake8-bugbear`, not of `tool.ruff.lint`. Fixed by adding
an explicit `[tool.ruff.lint]` header before `select`, with the
`flake8-bugbear` sub-table placed after it.

**Takeaway:** TOML's flat, order-dependent table scoping is genuinely
different from how nesting reads visually (indentation doesn't establish
hierarchy the way it does in YAML/Python) — worth double-checking table
order any time a new `[section]` gets added to `pyproject.toml`, not
just trusting where it visually looks like it belongs.

### 2026-08-18 — Learning: packaging a real installable CLI with `pyproject.toml`

**Context:** Phase 4A, Steps 1-2 — starting the CLI, which (unlike
`backend/`) needs to work as a command run from *any* directory,
including inside other repos like Voltra.

**Learning — why the CLI needs a `[project]` packaging section and
`backend/` never did:** `backend/` is only ever run in place (`uvicorn
app.main:app`, always from inside `backend/`), so it never needed to
become an installable package. The CLI's entire point is running from
arbitrary directories, which makes it a genuinely different category of
thing — the same kind of artifact as `requests` or `typer` itself, not
just more app code.

**Learning — `[project.scripts]` is what creates the actual command:**
```toml
[project.scripts]
journal = "journal_cli.main:app"
```
tells the packaging tool "install an executable named `journal` on PATH;
running it calls the object `app` inside `journal_cli/main.py`." Works
directly with a `Typer()` instance since Typer objects are callable —
no wrapper function needed.

**Learning — `[build-system]` boilerplate:** `requires = ["setuptools>=61.0"]`
+ `build-backend = "setuptools.build_meta"` just names which tool
actually builds/installs the package — `setuptools` is the standard,
unglamorous default, nothing exotic required for a project this size.

**Learning — separate dependency list from `backend/requirements.txt`:**
the CLI needs `typer`/`httpx`/`pydantic-settings` and has zero reason to
depend on `fastapi`/`sqlalchemy`/`alembic` — genuinely separate programs
sharing one repo, not one program split across folders.

**Design decision — CLI config reads only real env vars, no `.env`
file:** `backend/app/core/config.py` reads a `.env` sitting next to it
because `uvicorn` always runs from a known location. The CLI has no such
guarantee — it could run from Voltra, from `dev-journal`, from anywhere
— so there's no reliable relative path to a `.env` file. It reads
`DEV_JOURNAL_API_URL` from a real environment variable instead.

**Nice trick worth reusing — `pydantic-settings`' `env_prefix`:** setting
`env_prefix="DEV_JOURNAL_"` on a `BaseSettings` class means the `api_url`
field reads from `DEV_JOURNAL_API_URL` (prefix + uppercased field name)
instead of a bare `API_URL`. Namespacing env vars this way avoids ever
colliding with some unrelated `API_URL` that might already be set in
whatever shell the tool happens to run in — a real risk for anything
meant to run in arbitrary environments/shells (like this CLI), much less
of one for something like the backend that owns its own isolated `.env`.
General pattern worth reaching for on any future CLI/tool that reads
config from the environment rather than a known local file.

### 2026-08-18 — Learning: `journal_cli` imports don't resolve until the package is actually installed

**What happened:** `python -c "from journal_cli.config import get_settings; ..."`
raised `ModuleNotFoundError: No module named 'journal_cli'` — expected,
not a real bug, but worth logging as a procedural gotcha for next time.

**Why:** unlike `backend/app/...`, which works as an import purely by
virtue of being run with the right working directory (no install step,
just cwd on `sys.path`), the CLI is being built as a genuine installable
package (`cli/pyproject.toml`, Step 1). Nothing makes `journal_cli`
importable — from any directory, including `cli/` itself — until it's
actually installed with `pip install -e cli/`. Sanity-checking a CLI
package's imports has one extra prerequisite step compared to the
backend's app code.

**Takeaway:** for this project going forward, any `journal_cli.*` import
test needs `pip install -e cli/` to have already happened at least once
in the active venv — remember this before assuming a fresh
`ModuleNotFoundError` means broken code.

### 2026-08-18 — Learning: `pip install -e` (editable install)

**Context:** Installing the CLI package for the first time —
`pip install -e cli/`.

**Learning:** a normal `pip install` *copies* the package's files into
the environment's `site-packages` at that moment — if you edit the
source afterward, the installed copy doesn't change, you'd have to
reinstall to pick up edits. `-e` (editable install, sometimes called a
"develop install") instead links the environment directly to the source
directory (`cli/journal_cli/`), so any edit to those `.py` files takes
effect immediately the next time the command runs — no reinstall needed.

**Why it matters here specifically:** the CLI is under active development
(every step so far has involved editing `git_utils.py`/`client.py`/
`main.py` repeatedly) — a non-editable install would mean re-running
`pip install cli/` after every single change just to test it, which
would slow down the exact "write it, test it immediately" loop this
whole project has been following.

**Takeaway:** `-e` is the standard choice for any package you're actively
developing locally (this CLI, or dev-journal itself if it were ever
pip-installed); a plain `pip install` is for consuming a finished,
external package where you have no reason to expect the source to
change underneath you.

### 2026-08-18 — Roadblock: Typer silently drops the subcommand name when there's only one command

**Problem:** first real run of the installed CLI —
`journal log "testing the CLI for real"` — failed with `Got unexpected
extra argument(s) (testing the CLI for real)`, even though `main.py`
clearly defines `log` as a `@app.command()`.

**Investigation:** Typer has a default behavior where a `Typer()` app
with exactly *one* registered command auto-collapses — it stops
requiring the subcommand name entirely, so the app is invoked as
`journal "note text"` directly, not `journal log "note text"`. Since the
CLI only had the single `log` command defined, Typer expected the bare
form; `log` itself got parsed as the `note` argument, leaving the actual
note text as an unexpected leftover argument.

**Decision/fix:** rather than adopt the collapsed `journal "note"` form,
added an empty `@app.callback()` right after `app = typer.Typer()`.
Defining any top-level callback signals to Typer "this is a real
multi-command group," which disables the auto-collapse even with just
one command registered. Kept the explicit `journal log "..."` syntax on
purpose — matches the roadmap's intended interface, and leaves room for
future subcommands (e.g. a hypothetical `journal search`) without
another syntax change later.

**Takeaway:** a CLI framework's "helpful" default (fewer keystrokes for
the common single-command case) can silently conflict with a
deliberately-chosen interface — worth checking a framework's collapsing/
shortcut defaults against the actual intended command shape before
assuming a failing invocation means the code itself is wrong.

### 2026-08-18 — Milestone: first real `journal log` command, end to end

**What happened:** `journal log "testing the CLI for real"` — a real,
installed, globally-available CLI command — successfully created and
persisted an entry through the full stack: Typer parses the command,
`git_utils.detect_project` auto-detects `project='dev-journal'` from the
git remote, `client.create_entry` POSTs it over real HTTP to the running
FastAPI backend, which writes it to `dev_journal.db`. Confirmed visible
via `GET /entries` and FastAPI's auto-generated `/docs` UI.

**Why this matters:** this is the actual "usable with Voltra" bar being
crossed — everything from Phase 1 onward (config, DB session, model,
migrations, service layer, router, and now this installable CLI) was
infrastructure in service of this one command working from an arbitrary
directory. Cross-repo detection itself is still unverified against a
real second repo (Voltra) — that's the next concrete test.

**Takeaway:** worth noting how many distinct pieces had to be correct
simultaneously for this to work (packaging, dependency injection, git
subprocess calls, HTTP client, database session lifecycle) — a good
one-line answer to "what does this project actually demonstrate" for a
portfolio context.

### 2026-08-18 — Learning: FastAPI auto-generates interactive API docs for free

**Finding:** `http://127.0.0.1:8000/docs` serves a full interactive UI
(Swagger UI) listing every route the app defines — `/health`,
`POST /entries`, `GET /entries`, `GET /entries/{id}` — generated
automatically from the FastAPI app and its Pydantic schemas, no extra
code or config written for it. Each endpoint can be expanded and
actually called from the browser (fill in a form, hit "Execute," see
the real response), which is a much faster way to poke at the API than
constructing `curl`/`curl.exe` commands by hand.

**Why it works with zero setup:** FastAPI derives the whole docs page
from things that already exist for other reasons — the route
decorators, the `response_model`s, and the Pydantic schemas' field
types/validation. It's a side effect of writing typed, schema-driven
code, not a separate thing to build or maintain.

**Takeaway:** worth reaching for `/docs` as the default way to manually
poke at the API going forward, instead of `curl.exe` — faster, shows
request/response shapes directly, and doubles as living documentation
for anyone else looking at the project (nice thing to point to for the
portfolio angle too).

### 2026-08-18 — Milestone: cross-repo capture verified for real, from Voltra

**What happened:** ran `journal log "some real note about Voltra"` from
inside the actual Voltra repo (`C:\Users\virdi\OneDrive\Desktop\Volentia\voltra`,
a completely different folder tree from `dev-journal`), with the
`dev-journal` backend running separately. Auto-detection correctly
resolved `project='voltra'` from git with no `--project` flag needed,
and the entry (`#3`) landed in `dev-journal/backend/dev_journal.db` —
confirming the CLI's install (in the `dev-journal` venv) is fully
decoupled from Voltra's own dependencies/venv, and that `git_utils.py`'s
read-only git calls don't touch Voltra's repo state at all.

**Why this is the actual milestone, not just another test:** this is the
literal hard requirement that shaped Phase 4A's entire design from the
start — the CLI needed to work from inside other codebases, not just
dev-journal itself. Everything from the package-not-just-script decision
(`cli/pyproject.toml`, `pip install -e`) through the git auto-detection
logic was built specifically to make this moment possible. It's now
verified against the real target project, not a hypothetical.

**Takeaway:** the "usable with Voltra" bar set all the way back when
scoping the roadmap is now actually crossed — dev-journal can capture
real entries while working in Voltra today, even before Claude
structuring (3B) or search (3C) exist.

### Open Questions / To Revisit

- How much autonomy before requiring confirmation on auto-structuring entries?
- At what entry volume should the "scaling wall" naturally appear, or should it be simulated for the demo?
- Whether to add passive capture (git hooks, terminal hooks) as part of this project or defer to a v2

---

## Session Log

### 2026-08-16 — Journal moved from Notion into the repo

**Decision:** Migrated this journal from Notion into `context/journal.md`,
git-tracked, replacing the earlier decision to keep Notion as source of
truth.

**Why:** The end goal is a tool that scans repos directly to extract
context (roadblocks, learnings, decisions) and generate LinkedIn post
ideas. Repo-local markdown lets that tool read files directly — no Notion
API auth, no page-parsing integration — and it matches the retrieval
pattern the dev-journal app itself is being built around, instead of
using a different mechanism for the meta-journal about building it.

**Tradeoff accepted:** losing Notion's editing ergonomics (comments, rich
blocks, mobile capture) in exchange for zero integration surface between
the eventual content-generator tool and this data.

**Takeaway:** for personal-scale logging that a tool will later parse
programmatically, prefer the format the tool will actually consume over
the format that's nicest to author in.

### 2026-08-16 — GitHub template file discovery + PR template not showing

**Problem:** Added `.github/PULL_REQUEST_TEMPLATE.md`, but the template
didn't appear when opening a PR on GitHub.

**Investigation:** Two separate gotchas stacked here:
1. GitHub reads the PR template from the **base branch** of the PR (`main`), not the branch being compared from. The file only existed on `divjot-branch`, so it was invisible until merged.
2. GitHub's template discovery is filename-based, not folder-based: it looks for the literal name `pull_request_template` (case-insensitive; `.md`/`.txt`/no-extension all work) in exactly one of three locations — repo root, `.github/`, or `docs/`. Being inside `.github/` doesn't make an arbitrary filename auto-apply; the name has to match. (Multiple selectable templates use a `.github/PULL_REQUEST_TEMPLATE/` folder instead, chosen via `?template=` in the PR-creation URL.)

**Fix/Outcome:** Opened the PR anyway knowing the template wouldn't render
this first time; it will auto-apply to every PR after this one merges to
`main`.

**Takeaway:** repo-level GitHub config (PR/issue templates, CODEOWNERS,
workflows) only takes effect from the default branch — always ask "is
this file actually merged to main yet?" before assuming GitHub picked it
up.

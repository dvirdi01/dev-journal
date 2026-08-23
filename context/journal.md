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

### 2026-08-22 — Decision: prioritize Phase 3B/3C over CLI installability

**Context:** Was mid-discussion on making the `journal` CLI installable by
anyone via `pip`/`pipx` straight from GitHub (`pip install
git+https://github.com/dvirdi01/dev-journal.git#subdirectory=cli`), which
is mechanically real but only solves distribution — a stranger installing
it still hits a `ConnectError` immediately since the CLI is hardwired to
`127.0.0.1:8000` and there's no backend for them to talk to
([config.py](../cli/journal_cli/config.py)).

**Decision:** Deprioritize CLI installability/packaging polish. Prioritize
finishing retrieval — Phase 3B (Claude structuring: raw note → structured
entry) and 3C (query/search) — instead.

**Why:** The project's actual LinkedIn engagement hook isn't "you can pip
install my CLI" (most viewers won't install anything regardless of
polish) — it's Phase 5's planned scaling-wall comparison: a concrete
measured claim (context-stuffing cost vs. retrieval cost once real
entries exist). That comparison needs real structured entries and a
working query path first, which 3B/3C provide and installability doesn't.

**Tradeoff accepted:** the repo stays a personal-only tool (single
hardcoded backend URL, no auth/multi-tenant story) for now — fine for a
portfolio/LinkedIn demo, revisit only if the goal shifts to real external
users.

**Takeaway:** when scoping a portfolio project, weigh each next step by
"does this strengthen the actual content/demo story" rather than
generic "more professional/polished" instincts — installability felt
like the more impressive next step but wasn't the one that produces the
post.

### 2026-08-22 — Decision: system prompt design and model choice for Claude structuring (Phase 3B)

**Context:** Building `structure_note()` in
[claude_structuring.py](../backend/app/services/claude_structuring.py),
which turns a raw CLI note into the `StructuredFields` (context/problem/
investigation/fix/takeaway) via `client.messages.parse(...,
output_format=StructuredFields)`.

**Decision — system prompt:** Went beyond a generic "extract structure"
instruction to explicitly spell out what each of the six `entry_type`
values means (note/decision/bug/milestone/learning/question), plus a
terseness/no-fabrication rule ("leave a field null rather than guessing
or padding it out... do not invent detail, backstory, or elaboration the
note doesn't contain").

**Why:** Real notes logged via `journal log` are short CLI one-liners,
not paragraphs. Without the entry_type vocabulary, Claude had no signal
for which fields a given type should even plausibly fill (e.g. a
`decision` entry has no real `investigation`); without the terseness
rule, a one-line note risked getting an inflated, partly-invented
`context` paragraph just to fill space. Per-field Pydantic `Field(...,
description=...)` text is also sent to Claude as part of the JSON
schema (via `output_format`), so those descriptions already do some of
this work — the system prompt adds the type-vocabulary and
anti-fabrication framing that individual field descriptions can't.

**Decision — model:** Chose Claude Sonnet 5 over Opus 5 (skill default)
and Haiku 4.5 for `structure_note()`.

**Why:** This call runs synchronously inside `POST /entries`, which the
CLI blocks on — so its latency is directly felt as "how long does
`journal log` take to return." It's also a bounded extraction task
(short note in, five short fields out), not open-ended reasoning, so
Opus 5's extra adaptive-thinking cost buys little here. Sonnet 5 is the
middle point: still strong at classification/extraction, meaningfully
faster/cheaper than Opus for a per-call latency the user feels every
time.

**Follow-up planned:** Pull the model string into a `_MODEL` constant
and add `time.perf_counter()` timing around the API call (log on both
success and failure) — not for this call alone, but so that later,
swapping `_MODEL` between Sonnet 5 / Opus 5 / Haiku 4.5 and re-running
the same notes gives a ready-made latency (and failure-rate) comparison
table. This extends Phase 5's planned "scaling wall" LinkedIn post to
also cover a model-tier tradeoff, not just context-stuffing vs.
retrieval.

**Takeaway:** cheap instrumentation (one timing constant + one log line)
added at build time can turn a future one-off experiment into "just
read the logs" — worth doing whenever the future comparison is already
foreseeable, not just when you're about to run it.

### 2026-08-22 — Bug: CLI's `httpx.post` default timeout too short for a Claude-backed endpoint

**Problem:** After wiring `structure_note()` into `create_entry()` (Phase
3B) and adding a real `ANTHROPIC_API_KEY`, running `journal log "..."`
threw `httpx.ReadTimeout` in the CLI with a full traceback, even though
nothing about the request itself was wrong.

**Investigation:** Checked the backend's own terminal output (the
running `uvicorn` process) rather than assuming the request had failed
server-side:
```
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:app.services.claude_structuring:Claude structuring ok model=claude-sonnet-5 duration=5.69s
```
The Claude call succeeded in 5.69s and the entry committed to the DB
fine (confirmed via `GET /entries` — entry #4 existed with real
structured fields). The CLI's `httpx.post(...)` call in
[client.py](../cli/journal_cli/client.py), however, passed no `timeout`
argument, so `httpx` used its default — 5 seconds total. The CLI gave up
and raised client-side one moment before the backend would have replied.

**Fix:** Added `timeout=30.0` to the `httpx.post(...)` call in
`client.py` — comfortable headroom above the measured 5.69s, including
room for the model to later be swapped to Opus 5 (likely slower) for the
Phase 5 model-latency comparison without the CLI falsely reporting
failure on a request that actually succeeded.

**Takeaway:** `httpx`'s 5s default timeout is fine for a typical
CRUD-style REST endpoint but was never designed around "this endpoint
makes a real LLM call before replying" — any client hitting an
LLM-backed endpoint needs its timeout raised explicitly, since default
HTTP client timeouts assume millisecond-scale responses. Also: when a
client-side exception fires, check the *server's* logs before assuming
the request failed — the backend can succeed while the client alone
gives up.

### 2026-08-22 — Decision: park automatic session-capture, build a manual `/journal` command instead

**Context:** Explored whether the CLI could auto-capture *how* a bug was
actually debugged (via Claude Code, manually, or another agent CLI)
instead of requiring the user to type a summary by hand — the concern
being that manual note-typing risks making the tool no better than
pasting into a personal notes app.

**Research (verified against official docs, not blog sources):**
Claude Code hooks can technically do this — `SessionEnd` fires once per
session with a `transcript_path` to the full JSONL conversation, and a
hook can shell out to run `journal log` with real content
(`~/.claude/settings.json` or project `.claude/settings.json`; hooks
block execution up to a configurable timeout, default 1.5s, up to 60s
max — not fire-and-forget).

**Why rejected as the primary mechanism (two separate problems found):**
1. **"Session" ≠ "one topic."** A Claude Code session is tied to
   process lifetime, not topic boundaries — this user's actual pattern
   is one long-running session that's rarely if ever closed, covering
   many unrelated bugs/decisions/learnings over days. `SessionEnd`
   would almost never fire, and when it did, would bundle everything
   into one undifferentiated blob rather than the separate entries
   actually wanted.
2. **Segmentation (splitting a transcript into multiple entries) is a
   solvable schema problem, but it doesn't solve the deeper one:
   significance.** An automatic extractor has no concept of what's
   *worth* logging vs. noise — e.g. entry #4
   (`"testing after claude restructuring"`) was itself a throwaway test
   note that still produced an entry. The manual "log this" pattern
   used throughout this session's actual work implicitly filters
   signal from noise for free, because a human is choosing the moment;
   full automation would need to independently solve that judgment
   call, which is the actual hard, unsolved part of the feature — not
   a v1-vs-v2 detail.

**Decision:** Build a manual `/journal` Claude Code slash command next
(pulls minimal recent context, calls the existing structuring pipeline,
logs one entry) — preserves the human significance-judgment for free,
and is mostly wiring on top of what's already built (Phase 3B). Extend
`structure_note()`/`output_format` to return a *list* of entries rather
than one, since even a manual invocation may cover several topics in
one note.

**Idea documented but explicitly deferred — a "significance detector":**
instead of asking an LLM "is this important" (too vague, reproduces the
noise problem), use concrete signal proxies a hook can actually observe
— e.g. a `PreToolUse`/`PostToolUse` pattern of bash failing, retrying,
then succeeding (a bug fought and fixed); a git commit landing; the same
file/error recurring across many tool calls. Surface high-confidence
matches as a one-keystroke terminal confirm ("looks like you just fixed
X — log it? y/n"), not silent auto-logging — keeps the human as final
gate while removing the burden of remembering to invoke `/journal`
manually.

**Why this is deferred, not scoped in now:** it requires real
cross-invocation state Claude Code hooks don't provide natively (each
hook firing is stateless — detecting "3 failed attempts then success"
means building and maintaining an external rolling log of tool-call
outcomes ourselves, on every tool call, every session). And the proxy
signals are themselves an imperfect heuristic, not a solved version of
significance (a bash retry is often just a typo, not a real debugging
struggle) — this would be its own multi-iteration tuning project,
comparable in effort to everything built so far, sitting on top of a
`/journal` command that doesn't exist yet. Revisit only with real
evidence after `/journal` ships — e.g. repeatedly noticing "I wish I'd
logged that" after the fact — not preemptively.

**Takeaway:** when a feature's "automatic" version requires solving a
genuinely fuzzy judgment call (here: significance), don't let a clean
technical fix for an adjacent problem (segmentation) create false
confidence that the hard part is solved too. Sequencing manual-first and
gathering real evidence of a gap is cheaper than building speculative
infrastructure for a problem that might not exist in practice.

### 2026-08-22 — Bug: `/journal` custom command not registering — `allowed-tools` colon syntax invalid

**Context:** Built a `/journal` Claude Code slash command
([`.claude/commands/journal.md`](../.claude/commands/journal.md)) that
drafts a journal entry from recent conversation context and, after user
confirmation, runs `journal log` — a manual, lower-friction alternative
to typing a full summary by hand (chosen over automatic session/hook
capture, see the decision above).

**Learning — custom commands vs. Skills:** Claude Code's official docs
state commands and Skills are unified, not one deprecating the other:
*"Custom commands have been merged into skills. A file at
`.claude/commands/deploy.md` and a skill at
`.claude/skills/deploy/SKILL.md` both create `/deploy` and work the same
way. Your existing `.claude/commands/` files keep working."* Didn't know
this — assumed the flat-file `.claude/commands/<name>.md` format might
be legacy-only; it's current, documented, first-class.

**Problem:** After creating the file (and fixing an initial unrelated
mistake — the folder was named `claude/` instead of `.claude/`),
`/journal` still returned "no matching commands" in a brand new session,
even though other built-in slash commands worked fine.

**Investigation:** The frontmatter had
`allowed-tools: Bash(journal:*)` — a colon-separated pattern. Checked
official docs again: the documented `allowed-tools` glob syntax is
**space**-separated (`Bash(git add *)`, `Bash(git commit *)`), not
colon-separated. Invalid/unrecognized frontmatter appears to make
Claude Code silently skip loading the whole command file — no visible
parse error, it just doesn't show up.

**Fix:** Changed to `allowed-tools: Bash(journal *)` (space instead of
colon), matching the documented pattern shape.

**Takeaway:** when a Claude Code custom command silently fails to
register, suspect frontmatter syntax first — invalid YAML or an
undocumented pattern shape fails closed with no error message, which
looks identical to "file not found" or "wrong location" from the
outside. Worth checking the exact documented examples (not inferring
syntax from adjacent tools' conventions) before assuming a location or
naming problem.

**Update — the syntax fix wasn't the actual root cause.** After fixing
`allowed-tools` and restarting VSCode fully, `/journal` *still* didn't
register — and neither did a trivial zero-frontmatter test command
(`.claude/commands/hello.md`, no `---` block at all), which ruled out
`journal.md`'s content entirely. Root cause: **the VSCode Claude Code
extension's chat panel doesn't read `.claude/commands/` at all — only
the standalone `claude` CLI does.** Confirmed by installing the CLI
(`npm install -g @anthropic-ai/claude-code`, not previously installed on
this machine — only the extension was present) and running `/hello` in
a terminal `claude` session, where it worked immediately.

**Resolution:** ran `/journal` in the standalone CLI terminal session —
it registered, drafted a note from recent conversation context, waited
for explicit confirmation as designed, and on confirming created entry
#6. First successful end-to-end run of the manual-capture design from
the decision above.

**Takeaway (extending the one above):** when a Claude Code feature
seems to not work despite correct files/syntax/location, consider that
the VSCode extension and the standalone CLI may not have full feature
parity — they're not guaranteed to be the same implementation moving in
lockstep. A trivial, content-free reproduction (the `hello.md` test)
isolated this far faster than continuing to debug `journal.md`'s
content would have. Going forward, `/journal` (and any future custom
commands) needs to be run from a terminal `claude` session, not this
VSCode chat panel.

### 2026-08-22 — Decision: work primarily from the terminal `claude` CLI going forward

**Context:** With `/journal` confirmed only runnable from the terminal
CLI (not the VSCode extension panel), a new problem surfaced: the actual
debugging/decision conversations for this project have been happening
*in the VSCode extension panel* (this session). A `/journal` invocation
from a fresh terminal session has no "recent conversation" to draw
from — its whole design assumes it's running in the same session where
the work happened.

**Investigated:** whether `claude --resume` from a terminal could
reopen *this exact* VSCode session, giving a terminal-driven `/journal`
call access to this session's full history. Docs (checked via research
agent) stated: *"The extension and CLI share the same conversation
history"* — implying this should work.

**Empirically disproven:** Ran `claude --resume` in a terminal — the
picker showed only two sessions, and this session (auto-titled "project
stage check" in the VSCode panel) was not among them. Confirmed further
by resuming both listed sessions and asking each a fact stated
explicitly in *this* conversation (the $5 prepaid API credit,
auto-reload off) — neither knew it; one explicitly said it had no
access to that information. So despite what the docs claim, this
specific VSCode session is not reachable from the terminal CLI's resume
mechanism in this setup — the practical reality contradicted the
documented claim.

**Decision:** Use the terminal `claude` CLI as the primary workspace
for development work going forward, not the VSCode extension panel.
Reasoning: `/journal`'s core design (drafting from "recent
conversation") only holds when the debugging/decision work and the
`/journal` invocation happen in the same session — which is only
reliably true within one interface. The terminal CLI supports both
custom commands *and* same-interface session resumption; the VSCode
panel supports neither for this purpose. This current conversation
stays as the historical record up to this point; it does not carry
forward automatically.

**Tradeoff accepted:** losing whatever VSCode-panel-specific ergonomics
existed (inline diffs, IDE integration, etc. — not deeply evaluated) in
exchange for `/journal` actually working as designed on new work,
without falling back to manually retyping summaries (Option B,
considered and rejected as mostly defeating the point of building the
command).

**Takeaway:** a documented claim about cross-interface feature parity
(the "shared conversation history" claim) turned out not to hold in
practice — worth remembering generally: even docs-verified research
(useful and necessary, per the hooks/commands research earlier) can
still be wrong or environment-dependent, and a direct empirical test
(try it, ask a fact only the real session would know) is the actual
tie-breaker when documented behavior and observed behavior disagree.

### 2026-08-22 — Learning: Claude Code has no passive visibility into other terminals, and a "journal" naming collision

**Learning — no passive terminal visibility:** confirmed (asked
directly, in the new terminal `claude` session) that Claude Code cannot
see output from a separate terminal window/process — e.g. an error in
the PowerShell tab running `uvicorn` isn't visible unless it's pasted in
manually, or the command is re-run through Claude's own tool calls
instead. Relevant now that the standard workflow is two terminals side
by side (one running the backend, one running `claude`) — errors in the
backend terminal need to be copy-pasted over, not assumed visible.

**Learning — "journal" is an overloaded term in this project, causing
real confusion:** saying "log this finding" in the terminal session
(intending "add this to `context/journal.md`") instead triggered the
`/journal` slash command's structured-DB-entry flow (draft
raw_note/entry_type → `journal log` → SQLite row) — because "journal
entry" genuinely means two different things here: an edit to this
markdown build-log file, vs. a row in the app's own `Entry` table. The
`/journal` command's existence makes "log this"/"journal entry" default
toward the DB-write interpretation, not the file-edit one, since that's
the more recently-discussed meaning in a session that's been testing
`/journal`.

**Resolution for now:** be explicit about which one is meant — e.g. "add
this to `journal.md`" vs. "log this via `/journal`" — rather than relying
on "log this" alone. No renaming done yet; worth considering later
if the ambiguity keeps causing friction (e.g. renaming the CLI/command
to something like `entry` or `dj-log` to free up "journal" for referring
unambiguously to `journal.md`).

**Takeaway:** naming two related-but-distinct things in a project with
overlapping vocabulary ("journal" for both the human build-log and the
app's own core noun) creates exactly this kind of ambiguity — worth
choosing more distinct terms earlier, though not disruptive enough here
to warrant a rename mid-build.

### 2026-08-22 — Decision: user builds Phase 3C code directly, Claude teaches instead of implementing

**Decision:** For this project specifically, Claude writes no feature
code going forward (migrations, endpoints, services, etc.) — the user
writes it themselves, with Claude explaining approach/rationale and
handling only bug fixes and docs/journal updates.

**Why:** Claude started writing the Phase 3C FTS5 search implementation
unprompted after the user said "let's start 3C"; the user stopped it
immediately — this is a learning project, not a delegate-the-build one.

**Takeaway:** "let's start [phase]" is agreement to move forward on the
phase, not an invitation to write the code — worth checking which is
meant before implementing, especially on a project explicitly framed as
hands-on learning.

### 2026-08-22 — Milestone: Phase 3C search infrastructure in progress (FTS5 schema + service function)

**Context:** Building Phase 3C (retrieval/query) per the roadmap — SQLite
FTS5 keyword search, chosen over embeddings/RAG for v1 (see "Where RAG
Actually Belongs" above: only the "have I seen this before" flow is
genuinely RAG, and the project's honest-scaling-wall narrative wants
"start simple" before adding that).

**Built so far, user-authored with Claude explaining design decisions:**
1. `backend/app/core/search.py` — `FTS_SETUP_SQL`/`FTS_TEARDOWN_SQL`, a
   shared list of raw SQL statements (not one multi-statement string,
   since SQLite's driver executes one statement per call) so the
   Alembic migration and future test fixtures can't drift apart.
2. An `entries_fts` FTS5 virtual table via external-content mode
   (`content='entries', content_rowid='id'`) — keeps `entries` as the
   single source of truth instead of duplicating data into the search
   index — plus three triggers (`entries_ai`/`entries_ad`/`entries_au`)
   that manually sync `entries_fts` on insert/update/delete, since
   external-content FTS5 tables don't auto-sync. Applied via Alembic
   migration `f2617d5f7c63` (`down_revision` chained to `c15bab78e938`);
   verified against `dev_journal.db` directly with `sqlite3` — table,
   shadow tables, and all three triggers present.
3. `search_entries()` in `app/services/entries.py` — joins `entries` to
   `entries_fts` on `rowid`, filters with `MATCH :q` (+ optional
   `project`), orders by `bm25(entries_fts)` ascending (FTS5's bm25 is
   more-negative-is-better, opposite the usual intuition). Uses
   SQLAlchemy `text()` with bound params rather than f-string SQL
   (injection risk), then re-fetches each result via `db.get(Entry, id)`
   since raw `execute()` rows aren't ORM objects `EntryRead` can
   serialize from — an extra query per result, acceptable at this
   project's scale.

**Still open:** the `/search` endpoint (route-ordering gotcha: must be
registered before `GET /{entry_id}` or FastAPI's path matching will
swallow it), and syncing the test fixture in `test_entries.py` — it
builds tables via `Base.metadata.create_all()`, which never runs Alembic
migrations, so `entries_fts` won't exist there until `FTS_SETUP_SQL` is
also executed against the test DB.

### 2026-08-22 — Gotcha: FastAPI route ordering — `/{entry_id}` would swallow `/search`

**Problem (caught before writing the code, not after):** `entries.py`'s
existing routes are `POST /entries`, `GET /entries`, then
`GET /entries/{entry_id}`, in that order. Adding `GET /entries/search`
*after* `{entry_id}` would break it — FastAPI/Starlette match routes in
registration order and stop at the first match, and `{entry_id}` is a
path parameter that matches any single segment, including the literal
string `"search"`. A request to `/entries/search?q=timeout` would hit
`get_entry` first, with FastAPI trying (and failing) to parse `"search"`
as `entry_id: int`, never reaching the actual search logic.

**Fix:** register the new `/search` route *before*
`@router.get("/{entry_id}")` in the file — plain literal paths need to
come before parameterized ones that could shadow them.

**Takeaway:** any time a new route is added to a router that already has
a `/{param}` catch-all-shaped route, check registration order first —
this class of bug is silent until the specific overlapping path is
actually requested, so it's cheap to get right upfront and easy to miss
in review otherwise.

### 2026-08-22 — Bug: `uvicorn --reload` stopped picking up file changes after the first reload

**Problem:** After adding the `/search` route to `entries.py`, a live
request to `/entries/search?q=timeout` still returned the *old* 3-route
behavior (a 422 trying to parse `"search"` as `entry_id: int`) — the
exact failure mode the route-ordering fix above was supposed to prevent,
even though the file on disk was already correctly ordered.

**Investigation:** Checked the running server's log output directly
(possible specifically because this session's backend was started via
Claude's own background Bash tool call, not a separate terminal — see
the earlier "no passive terminal visibility" learning). Found only one
`WatchFiles detected changes... Reloading` line, triggered by
`app/core/search.py`'s creation — no reload fired for the later edits to
`services/entries.py` or `api/entries.py`. The running process was still
serving code from before those edits.

**Fix:** Stopped the background task and restarted `uvicorn app.main:app
--reload` fresh. Re-tested `/entries/search?q=route` — correctly
returned the matching entry.

**Takeaway:** don't assume `--reload` fired for every save — if a code
change doesn't seem to take effect, check the server's actual log output
for a `Reloading` line covering that file before concluding the code
itself is wrong. A full restart is a cheap way to rule this out.

### 2026-08-22 — Milestone: Phase 3C (FTS5 search) complete, end to end

**Outcome:** All five pieces built and verified working together:
`app/core/search.py` (shared DDL), Alembic migration `f2617d5f7c63`,
`search_entries()` in the service layer, the `GET /entries/search`
route, and a `test_search_entries_finds_match` test in
`test_entries.py` (fixture updated to run `FTS_SETUP_SQL` against the
in-memory test DB after `Base.metadata.create_all()`, since Alembic
migrations never run there). Full test suite passes. Manually verified
via curl: searching "route" against real logged entries correctly
returns only the matching one.

**Process note:** built entirely by the user, with Claude limited to
explaining design decisions and doing bug fixes/docs — see the earlier
"user builds Phase 3C code directly" decision entry.

**Where this leaves the roadmap:** Phase 3 (Backend API) is now fully
done — 3A (create/list/get), 3B (Claude structuring), 3C (FTS5 keyword
search). Semantic/embedding-based search remains explicitly out of
scope per the "Where RAG Actually Belongs" framing (only the "have I
seen this before" flow is genuinely RAG, and that's deferred until
FTS5's limits are actually felt at real entry volume). Next up per the
roadmap: Phase 4 (Interfaces) — CLI installability (deprioritized
2026-08-22 in favor of 3B/3C, now unblocked) and/or the Streamlit
frontend (chat interface + basic dashboard).

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

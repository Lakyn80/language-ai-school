# Language AI School

Language AI School is a modular backend platform for scenario-based language learning.
It combines:

- Retrieval-Augmented Generation (RAG) from local world data
- CEFR-aware lesson generation
- Scene management in PostgreSQL
- Reading comprehension evaluation with multilingual feedback
- Strict module boundaries enforced by architecture tests

The backend is implemented with FastAPI and is designed to run in Docker or locally.

## Table of Contents

- Overview
- Current Status
- Repository Structure
- Core Architecture
- Data Model
- API Reference
- End-to-End Flows
- Configuration and Environment Variables
- Run with Docker
- Run Locally (without Docker)
- Database and Migrations
- RAG Ingestion and Indexing
- Testing and Quality Gates
- Modularity Rules
- Known Limitations
- Operational Notes
- Development Workflow
- LangChain/LangGraph Triggers
- Roadmap

## Overview

Core capabilities currently available:

- Health endpoint
- Titles endpoint (archetype catalog)
- RAG search endpoint over local world JSON files
- Lesson generation endpoint using:
  - world context from RAG
  - scene context from DB
  - DeepSeek chat completions
  - CEFR difficulty audit
  - optional persistence of generated lessons
- Full scenes CRUD (PostgreSQL)
- Reading comprehension evaluation:
  - translation cache layer
  - semantic similarity
  - missing/hallucination detection
  - CEFR pass/fail scoring
  - feedback text in multiple native languages

## Current Status

As of the current repository state:

- Backend tests pass (`23 passed`).
- Docker Compose stack includes backend, Redis, and PostgreSQL.
- Scene auto-seeding from JSON into DB is implemented.
- Lesson persistence in `lesson_generations` is implemented (feature-flagged).
- Story modes are implemented at the prompt/context style level (`strict`, `story`, `cinematic`).
- Architecture tests enforce strict module boundaries.

## Repository Structure

Top-level:

```text
.
|- backend/
|  |- app/
|  |  |- api/
|  |  |- core/
|  |  |- db/
|  |  |- modules/
|  |  |  |- health/
|  |  |  |- titles/
|  |  |  |- rag/
|  |  |  |- lessons/
|  |  |  |- scenes/
|  |  |  |- reading/
|  |  |- pedagogy/
|  |  |- shared/
|  |- alembic/
|  |- tests/
|- docker-compose.yml
|- docker-compose.dev.yml
|- dev.ps1
|- auto_test_deploy.ps1
```

Notes:

- `frontend-next/` exists but is currently empty.
- Root `requirements.txt` exists, but backend dependency management is primarily in `backend/requirements.txt`.

## Core Architecture

### Application bootstrap

- Entry point: `backend/main.py`
- App factory: `backend/app/core/app_factory.py`
- API router assembly: `backend/app/api/router.py`

### Module responsibilities

- `health`: service liveness
- `titles`: static archetype catalog from JSON
- `rag`: vector retrieval over local world data
- `scenes`: DB-backed scene CRUD + JSON-to-DB seeding
- `lessons`: orchestration, LLM call, difficulty audit, cache, persistence
- `reading`: HTTP module wrapper over pedagogy comprehension engine

### Supporting layers

- `app/pedagogy`: CEFR, language profiles, comprehension evaluation internals
- `app/db`: SQLAlchemy engine/session/base
- `app/shared`: cross-module infrastructure utilities (for example DB session management)

## Data Model

### Tables

`scenes`

- `id` (PK)
- `slug` (unique)
- `title`
- `description`
- `situation_text` (raw JSON payload stored as text)
- `category`
- `created_at`

`lesson_generations`

- `id` (PK)
- `level`
- `input_context`
- `result_json`
- `created_at`

### JSON data sources

- Worlds: `backend/app/data/worlds/*.json`
- Scene templates: `backend/app/data/scenes/*.json`
- Titles catalog: `backend/app/modules/titles/data/titles.json`

## API Reference

Base prefix: `/api`

### Health

- `GET /api/health/`
- Response:

```json
{
  "status": "ok",
  "service": "language-ai-school"
}
```

### Titles

- `GET /api/titles/`
- Returns:

```json
{
  "titles": [
    {
      "id": "secret_agent",
      "name": "Secret Agent Mission",
      "universe": "Global Intelligence Network",
      "language": "EN",
      "level": "A2",
      "description": "..."
    }
  ]
}
```

### RAG Search

- `POST /api/rag/search`
- Request:

```json
{
  "query": "secret_agent",
  "k": 3
}
```

- Response:

```json
{
  "query": "secret_agent",
  "results": [
    {
      "id": "secret_agent",
      "text": "{...world json...}"
    }
  ]
}
```

### Lesson Generation

- `GET /api/lessons/generate`
- Query params:
  - `title_id` (required)
  - `scene_id` (required)
  - `level` (required, CEFR)
  - `mode` (`strict|story|cinematic`, default `strict`)
  - `target_language` (default `en`)
  - `native_language` (default `ru`)

- Returns:
  - metadata (`level`, `mode`, `scene_id`, language params)
  - normalized `scene`
  - `difficulty` audit object
  - `context_used` (RAG docs)
  - `lesson` payload from LLM (or fallback shape)

### Scenes CRUD

- `GET /api/scenes`
- `GET /api/scenes/{slug}`
- `POST /api/scenes`
- `PUT /api/scenes/{id}`
- `DELETE /api/scenes/{id}`

Schema includes:

- `slug`, `title`, `description`, `situation_text`, optional `category`

### Reading Evaluation

- `POST /api/reading/evaluate`
- Request:

```json
{
  "level": "B1",
  "target_language": "en",
  "native_language": "cs",
  "text": "Original generated story...",
  "student_summary": "Student summary in native language..."
}
```

- Response:

```json
{
  "score": 74,
  "result": "PASS",
  "feedback_native": "...",
  "missing": [],
  "hallucinations": []
}
```

## End-to-End Flows

### Lesson generation flow

1. Validate mode.
2. Resolve language profiles.
3. Build lesson cache key.
4. Return cache hit if available.
5. Retrieve world context from RAG.
6. Load scene from DB (`slug = scene_id`), auto-seed if DB empty.
7. Build final context block (language + style + scene + retrieved world docs).
8. Call DeepSeek `/chat/completions`.
9. Validate JSON against lesson schema; fallback if invalid.
10. Compute CEFR difficulty audit.
11. Optionally persist generation to DB (`lesson_generations`).
12. Store in cache and return response.

### Reading evaluation flow

1. Translate student summary to target language (currently stub translator).
2. Compute semantic similarity.
3. Compute missing and hallucinated sentences.
4. Apply coverage penalty.
5. Evaluate CEFR threshold pass/fail.
6. Return score and native-language feedback.

## Configuration and Environment Variables

Defined in `backend/app/core/config.py`:

- `APP_NAME` (default: `Language AI School`)
- `API_PREFIX` (default: `/api`)
- `DEEPSEEK_API_KEY` (required for lesson generation)
- `DEEPSEEK_BASE_URL` (default: `https://api.deepseek.com`)
- `DEEPSEEK_MODEL` (default: `deepseek-chat`)
- `RAG_INDEX_PATH` (default: `app/modules/rag/index/titles.faiss`)
- `RAG_EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `REDIS_URL` (default: `redis://redis:6379/0`)
- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DB` (default: `language_ai_school`)
- `POSTGRES_USER` (default: `language_ai`)
- `POSTGRES_PASSWORD` (default: `language_ai_pass`)
- `LESSONS_PERSIST_GENERATIONS` (default: `false`)
- `LESSONS_CACHE_BACKEND` (default: `memory`; use `redis` in Compose)

## Run with Docker

From repository root:

```bash
docker compose up -d --build
docker compose exec -T backend alembic upgrade head
```

Optional (if RAG index needs rebuild):

```bash
docker compose exec -T backend python -m app.modules.rag.ingest
```

Open API docs:

- `http://localhost:8086/docs`

Health check:

- `http://localhost:8086/api/health/`

## Run Locally (without Docker)

### 1) Setup environment

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2) Configure env

Create `backend/.env` and set at least:

- Postgres connection vars
- `DEEPSEEK_API_KEY` (for lesson generation)
- Optional `LESSONS_CACHE_BACKEND`

### 3) Run migrations and ingest

```bash
alembic upgrade head
python -m app.modules.rag.ingest
```

### 4) Start app

```bash
uvicorn main:app --host 0.0.0.0 --port 8086 --reload
```

## Database and Migrations

- Alembic config: `backend/alembic.ini`
- Alembic environment script: `backend/alembic/env.py`
- Migrations directory: `backend/alembic/versions/`

Important note:

- Migration history contains intermediate revisions that are no-op (`pass`) before final scene table creation.
- Running `alembic upgrade head` applies the full chain safely.

## RAG Ingestion and Indexing

Ingestion script:

- `backend/app/modules/rag/ingest.py`

It:

1. Reads `backend/app/data/worlds/*.json`
2. Builds embeddings with SentenceTransformer
3. Stores index + documents in `backend/app/modules/rag/index/titles.faiss`

Search:

- `VectorStore.search(query, top_k)` returns matched document payloads.

## Testing and Quality Gates

Run all backend tests:

```bash
pytest -q backend/tests
```

Key test categories:

- API behavior (`health`, `titles`, lessons/reading endpoints)
- Lesson cache behavior
- Lesson service parsing/fallback logic
- Reading comprehension behavior
- Architecture/modularity boundaries

## Modularity Rules

The project enforces strict module boundaries:

- No cross-module imports to internal files (`app.modules.<other>.internal_file`)
- Use module public API (`app.modules.<module>`) only
- No direct dependency from modules to DB session internals (`SessionLocal`, `app.db.session`)
- Shared cross-cutting infrastructure goes under `app/shared`

Guard tests:

- `backend/tests/test_architecture_modularity.py`
- `backend/tests/test_modularity_boundaries.py`

## Known Limitations

- Translation in reading flow is currently a stub (returns original text).
- CEFR difficulty engine currently returns audit/instruction; it does not rewrite lesson text automatically.
- RAG index file extension is `.faiss`, but payload is serialized with `pickle` (index + docs object bundle).
- Dockerfile default CMD references `app.main:create_app`; in Compose this is overridden with `uvicorn main:app ...`.
- `frontend-next/` is currently empty.

## Operational Notes

- Compose sets:
  - `LESSONS_CACHE_BACKEND=redis`
  - `LESSONS_PERSIST_GENERATIONS=true`
- If Redis is unavailable, lesson cache logic falls back to in-memory cache.
- Scene auto-seed occurs when scenes are first queried and DB is empty.

## Development Workflow

Windows helper scripts:

- `dev.ps1`: local Docker dev workflow
- `auto_test_deploy.ps1`: test -> build -> up -> health-check sequence

Recommended flow before merge:

1. Run `pytest -q backend/tests`
2. Run `docker compose config`
3. Optionally run `alembic upgrade head` in container
4. Smoke test:
   - `GET /api/health/`
   - `GET /api/scenes`
   - `POST /api/rag/search`
   - `POST /api/reading/evaluate`
   - `GET /api/lessons/generate` (requires valid DeepSeek key)

## LangChain/LangGraph Triggers

Current recommendation:

- **KEEP THE CURRENT ARCHITECTURE** while the flow stays deterministic (`RAG -> context -> prompt -> JSON -> validation`).
- **DO NOT ADD LANGCHAIN/LANGGRAPH PREMATURELY** for simple single-path generation pipelines.

Adoption triggers (migrate only when one or more are true):

- **MULTI-STEP AGENTIC WORKFLOWS** are required (tool planning, branching, recovery paths).
- **STATEFUL GRAPH EXECUTION** is needed (checkpointing, resumable nodes, long-running orchestration).
- **MULTI-TOOL ROUTING WITH DYNAMIC DECISIONS** becomes a core runtime requirement.
- **PARALLEL TOOL EXECUTION + MERGE LOGIC** must be first-class and reusable across products.
- **MULTI-PROVIDER ORCHESTRATION** (fallback models, provider routing, policy-based selection) grows beyond simple adapters.
- **OBSERVABILITY AT GRAPH/NODE LEVEL** is required for production debugging and SLA reporting.

If none of the triggers above is present, the current modular FastAPI architecture is typically faster to maintain, easier to debug, and cheaper to operate.

## Roadmap

Potential next milestones:

- Real translation provider integration for reading evaluation
- CEFR rewrite pass (not only audit)
- Expanded worlds and title coverage
- Lesson history query endpoints
- Frontend implementation in `frontend-next/`

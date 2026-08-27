# Riwi Co. - Internal Messaging Platform & AI Copilot (RAG)

> **Complete internal communication and AI Copilot platform with Clean Architecture, PostgreSQL Row-Level Security (RLS), Keyset Pagination, and Angular 22 frontend.**

---

## Project Summary

This repository contains the complete solution for **Riwi Co.** business messaging and AI semantic search. It is designed to keep channel information isolated, provide good transaction performance, and offer clear intelligent assistance.

### Main Features

1. **Channel Membership Security (RLS):**
   - Native PostgreSQL policies with `NOBYPASSRLS`.
   - Actor identity propagation through `app.current_user_id`.
   - Full isolation between public and private channels.
2. **Scoped AI Copilot with RAG, Citations, and Clear Refusals:**
   - Vector creation with `text-embedding-3-small` and an HNSW index (`pgvector`).
   - Text generation with OpenAI `gpt-4o-mini` and prompt version `v1.yaml`.
   - Verifiable citations (`[msg-xxxx]`) and token auditing in `rw_copilot_logs`.
3. **Fast Indexed Keyset Pagination ($O(1)$):**
   - No `OFFSET` is used, so navigation remains smooth with large data volumes.
4. **Full-Text Lexical Search with Highlighting:**
   - Spanish `tsvector`/`tsquery` engine with snippets and highlighting (`ts_headline`).
5. **Modern Angular 22 Frontend:**
   - Standalone Components + NgRx Signal Store + Angular Material.
   - 3 integrated areas: Conversation, RAG Copilot, and Profile with token metrics.
   - Complete i18n support (Spanish / English).
   - Sharp visual style: rectangular borders without rounding (`0px`), Ubuntu font, Light Blue (`#38BDF8`) and Mint Green (`#10B981`) palette.

---

## System Architecture

```
                      ┌───────────────────────────────────────────────┐
                      │    Frontend: Angular 22 + Signal Store        │
                      │    (Port 4200 / Nginx)                        │
                      └───────────────────────┬───────────────────────┘
                                              │ HTTP / Bearer JWT
                                              ▼
                      ┌───────────────────────────────────────────────┐
                      │    Backend: FastAPI (Clean Architecture)      │
                      │    (Port 4000)                                │
                      └───────────┬───────────────────────┬───────────┘
                                  │                       │
           OpenAI SDK (RAG)       │                       │ asyncpg Pool
           gpt-4o-mini / Embed    ▼                       ▼ (Actor Propagation)
                      ┌──────────────────────┐ ┌──────────────────────┐
                      │    OpenAI API        │ │  PostgreSQL 16 RLS   │
                      │  (Prompt v1.yaml)    │ │  + pgvector (1536d)  │
                      └──────────────────────┘ └──────────────────────┘
```

---

## Test Users (Seed Data)

All users have the default password: `riwi2026!`

| User | Full Name | Corporate Email | System Role | Position | Assigned Channels |
|---|---|---|---|---|---|
| `smunoz` | Santiago Muñoz | `santiago.munoz@riwi.co` | `admin` | Tech Lead & Architect | `#general`, `#backend-dev`, `#devops-infra` |
| `crojas` | Camila Rojas | `camila.rojas@riwi.co` | `member` | Senior Frontend Developer | `#general`, `#frontend-design` |
| `nvega` | Néstor Vega | `nestor.vega@riwi.co` | `member` | Backend Developer | `#general`, `#backend-dev` |
| `vcastro` | Valentina Castro | `valentina.castro@riwi.co` | `member` | QA Engineer | `#general`, `#frontend-design` |
| `alopez` | Andrés López | `andres.lopez@riwi.co` | `member` | DevOps Engineer | `#general`, `#devops-infra` |

---

## Quick Start (Docker Compose)

### 1. Clone the repository and configure environment variables:
```bash
cp .env.example .env
```

### 2. Start the complete platform:
```bash
docker compose up --build -d
```

### 3. Access:
- **Frontend SPA:** [http://localhost:4200](http://localhost:4200)
- **Backend API Docs (Swagger):** [http://localhost:4000/docs](http://localhost:4000/docs)
- **Backend ReDoc:** [http://localhost:4000/redoc](http://localhost:4000/redoc)

---

## Running Validation Tests by Phase

### Phase 1: Database Validation (SQL, RLS, Procedures, Queries 1-4)
```bash
python3 scripts/test_phase1_validation.py
```

### Phase 2: FastAPI Backend and RLS Security Validation
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests -v
```

### Phase 3: Angular Frontend and Unit Specs Validation
```bash
cd frontend
npx ng test --no-watch
```

### Phase 4: End-to-End Integration Test
```bash
python3 scripts/test_phase4_e2e.py
```

---

## Repository Structure

```
chat_consultas_riwi/
├── backend/                  # FastAPI REST API (Clean Architecture)
│   ├── prompts/v1.yaml       # Versioned Copilot system prompt
│   ├── src/
│   │   ├── domain/           # Entities and Ports (Protocols)
│   │   ├── application/      # Use cases
│   │   ├── infrastructure/   # asyncpg, JWT, Hasher, and OpenAI repositories
│   │   └── presentation/     # Routers, Pydantic schemas, and middleware
│   └── tests/                # Automated pytest test suite
├── frontend/                 # Angular 22 SPA (Standalone + Signal Store)
│   ├── public/assets/i18n/   # Internationalization dictionaries (ES / EN)
│   └── src/app/
│       ├── core/             # Services, interceptors, guards, and models
│       ├── features/         # Conversation, RAG Copilot, and Profile
│       └── shared/           # Navbar, loading states, and pipes
├── sql/                      # DDL, RLS, function, query, and seed scripts
│   ├── 01_schema.sql         # DDL with the rw_ prefix and extensions
│   ├── 02_security_rls.sql   # Row-Level Security policies
│   ├── 03_functions_procedures.sql # Atomic logic and procedures
│   ├── 04_queries.sql        # 4 required SQL queries
│   └── 05_seed.sql           # Idempotent initial data
├── docs/                     # Formal technical documentation and reports
│   ├── normalization.md      # 0NF -> 3NF normalization and dependencies
│   ├── MER.png               # High-resolution entity-relationship diagram
│   ├── security_model.md     # Security and RLS documentation
│   ├── copilot_rag.md        # AI and context policy documentation
│   ├── architecture.md       # Design decisions and Clean Architecture
│   └── api-collection.json   # Exported OpenAPI 3.1 collection
├── scripts/                  # Utility scripts and test suites
├── docker-compose.yml        # Container orchestration
├── .github/workflows/ci.yml  # Automated CI/CD pipeline
└── README.md                 # General project documentation
```

# System Architecture: Messaging and AI Copilot Platform

**Project:** Riwi Co. Internal Messaging & AI Copilot Platform
**Architecture:** Clean Architecture (Hexagonal / Ports & Adapters)
**Database:** PostgreSQL 15+ (`bd_santiago_munoz_nakamoto`) with the `vector` extension
**Frontend:** Angular 22 Standalone + NgRx Signal Store  
**Backend:** Python 3.12 + FastAPI + asyncpg

---

## 1. Global Architecture View

```mermaid
graph TB
    subgraph CloudDeployment ["Infrastructure & Deployment"]
        FE_HOST["Frontend: Vercel / Nginx (Container)"]
        BE_HOST["Backend: Render / FastAPI (Docker Multi-stage)"]
        DB_HOST["Database: PostgreSQL 16 + pgvector (Managed/Docker)"]
    end

    subgraph FrontendArchitecture ["Frontend: Angular 22 Standalone"]
        UI_Z1["Zone 1: Conversation & Messaging"]
        UI_Z2["Zone 2: AI Copilot & RAG"]
        UI_Z3["Zone 3: Profile & Audit"]
        NGRX_S["State: NgRx Signal Stores (Conversation, Copilot, Profile)"]
        CORE_SVC["Core Services: AuthService, ApiService, I18nService"]
        INTERCEPTORS["Interceptors: Auth (JWT Refresh), Correlation ID"]
    end

    subgraph BackendArchitecture ["Backend: Clean Architecture"]
        subgraph PresentationLayer ["1. Presentation Layer"]
            ROUTERS["Routers: Auth, Channels, Messages, Users, Copilot"]
            SCHEMAS["Pydantic v2 DTOs (Request / Response)"]
            MIDDLEWARE["Middleware: Correlation (X-Correlation-Id), Auth, Error Handler"]
        end

        subgraph ApplicationLayer ["2. Application Layer (Use Cases)"]
            UC_AUTH["Auth: Login, RefreshToken"]
            UC_MSG["Messages: Keyset Listing, Send, Search, Edit, Delete"]
            UC_USER["Users: QueryUsers, EditDeleteUser (SP)"]
            UC_COP["Copilot: QueryCopilot (RAG), GetUsage"]
        end

        subgraph DomainLayer ["3. Domain Layer (Pure Core)"]
            ENTITIES["Entities: User, Channel, Message, CopilotLog"]
            PORTS["Ports (typing.Protocol): UserRepositoryPort, MessageRepositoryPort, LlmServicePort, etc."]
        end

        subgraph InfrastructureLayer ["4. Infrastructure Layer"]
            REPO_PG["Pg Repositories (asyncpg + SQL directo)"]
            SEC_PG["Database Pool + SET LOCAL app.current_user_id"]
            LLM_SVC["OpenAILlmService + Offline Deterministic Fallback"]
            AUTH_SVC["JwtService (HS256 + SHA-256) & Hasher (bcrypt)"]
        end
    end

    subgraph DatabaseLayer ["Database: PostgreSQL 16 + pgvector"]
        RLS_POL["Row-Level Security (rw_app_role NOBYPASSRLS)"]
        PROC_FN["Funciones & Procedimientos: rw_fn_send_message, rw_sp_query_users, rw_sp_edit_or_delete_user"]
        FTS_TRG["FTS: tsvector + GIN Trigger en español"]
        VEC_IDX["Vector: 1536-dim HNSW Index (Cosine Distance)"]
        TABLES["7 Tablas rw_*: users, channels, channel_members, messages, read_receipts, copilot_logs, refresh_tokens"]
    end

    %% Frontend -> Backend connections
    UI_Z1 --> NGRX_S
    UI_Z2 --> NGRX_S
    UI_Z3 --> NGRX_S
    NGRX_S --> CORE_SVC
    CORE_SVC --> INTERCEPTORS
    INTERCEPTORS -- "HTTPS REST + JWT Bearer" --> ROUTERS

    %% Internal backend flow
    ROUTERS --> UC_AUTH & UC_MSG & UC_USER & UC_COP
    UC_AUTH & UC_MSG & UC_USER & UC_COP --> PORTS
    ENTITIES --- PORTS
    REPO_PG -.->|Implements| PORTS
    LLM_SVC -.->|Implements| PORTS
    REPO_PG --> SEC_PG
    SEC_PG -- "SET LOCAL + SQL" --> DatabaseLayer
```

---

## 2. Sequence Diagram: AI Copilot RAG Flow with RLS Security

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Riwi User
    participant FE as Angular Copilot (Zona 2)
    participant API as FastAPI Router (/api/copilot/query)
    participant Pool as asyncpg Pool (Actor Context)
    participant DB as PostgreSQL (pgvector + RLS)
    participant LLM as OpenAI LLM Service / Fallback

    Usuario->>FE: Enters a natural-language question
    FE->>API: POST /api/copilot/query (Bearer JWT)
    API->>API: Extracts and validates actor_id from JWT
    API->>LLM: Genera embedding para la consulta (text-embedding-3-small)
    LLM-->>API: Vector flotante de 1536 dimensiones
    API->>Pool: get_connection_with_actor(actor_id)
    Pool->>DB: BEGIN TRANSACTION + SET LOCAL app.current_user_id = '<actor_id>'
    API->>DB: SELECT con distancia coseno (<=>) filtrando rw_is_channel_member(channel_id)
    Note over DB: PostgreSQL runs the vector search ONLY on messages<br/>from channels where the authenticated user is an active member.
    DB-->>API: Relevant messages with context and [msg-XXXX]
    
    alt Context is available in authorized channels
        API->>LLM: Loads prompts/v1.yaml + authorized messages + question
        LLM-->>API: Generated answer with structured citations
    else No authorized messages or outside channel
        API->>LLM: Loads prompts/v1.yaml + empty context
        LLM-->>API: Clear refusal: "I do not have access to information about that topic..."
    end

    API->>DB: INSERT INTO rw_copilot_logs (tokens, model, query, response)
    API->>Pool: COMMIT TRANSACTION
    API-->>FE: 200 OK (answer, citations, model, tokens_used)
    FE-->>Usuario: Renders an interactive answer with clickable citation cards
```

---

## 3. Relational Data Model (3NF Normalization)

The model has 7 tables normalized to Third Normal Form (3NF). All tables use the required `rw_` prefix:

```mermaid
erDiagram
    rw_users ||--o{ rw_channels : "crea"
    rw_users ||--o{ rw_channel_members : "pertenece"
    rw_channels ||--o{ rw_channel_members : "contiene"
    rw_users ||--o{ rw_messages : "escribe"
    rw_channels ||--o{ rw_messages : "aloja"
    rw_messages ||--o{ rw_read_receipts : "registra_lectura"
    rw_users ||--o{ rw_read_receipts : "lee"
    rw_users ||--o{ rw_copilot_logs : "consulta_ia"
    rw_users ||--o{ rw_refresh_tokens : "posee_sesiones"

    rw_users {
        uuid id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        varchar display_name
        varchar role "admin | member"
        varchar position
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    rw_channels {
        uuid id PK
        varchar name UK
        text description
        varchar type "public | private"
        uuid created_by FK
        boolean is_archived
        timestamptz created_at
        timestamptz updated_at
    }

    rw_channel_members {
        uuid id PK
        uuid channel_id FK
        uuid user_id FK
        varchar role "owner | member"
        timestamptz joined_at
    }

    rw_messages {
        uuid id PK
        varchar msg_ref "indexado parcialmente"
        uuid channel_id FK
        uuid author_id FK
        text content
        text original_content "auditoría histórico"
        tsvector search_vector "FTS español"
        vector embedding "1536 dims HNSW"
        boolean is_edited
        timestamptz edited_at
        boolean is_deleted "soft-delete"
        timestamptz deleted_at
        varchar status "pending | sent | failed"
        timestamptz created_at
        timestamptz updated_at
    }

    rw_read_receipts {
        uuid id PK
        uuid message_id FK
        uuid user_id FK
        timestamptz read_at
    }

    rw_copilot_logs {
        uuid id PK
        uuid user_id FK
        text query
        text response
        integer prompt_tokens
        integer completion_tokens
        integer total_tokens
        varchar model
        varchar prompt_version
        timestamptz created_at
    }

    rw_refresh_tokens {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        timestamptz expires_at
        boolean is_revoked
        timestamptz created_at
    }
```

---

## 4. Security and Isolation Strategy

1. **Database Role without Superuser Privileges:**
    - The `rw_app_role` role is created with the `NOBYPASSRLS` clause.
    - Physical `DELETE` permissions are revoked on all operational tables.
2. **Actor Propagation:**
    - Each authenticated HTTP request gets the `user_id` from the JWT verified by the backend.
    - Before any query runs, the `asyncpg` pool executes `SET LOCAL app.current_user_id = '<actor_id>'` inside a transaction.
3. **RLS Security Functions:**
    - `rw_is_channel_member(p_channel_id)`: Checks the current user's membership in the requested channel in $O(1)$.
    - RLS policies automatically apply to `SELECT`, `INSERT`, and `UPDATE`.

---

## 5. Frontend Design (Angular 22 Standalone)

- **NgRx Signal Stores:** Predictable and reactive state management with Angular Signals:
    - `ConversationStore`: Active channels, deferred keyset pagination, send states (`pending`, `sent`, `failed`), and FTS search.
    - `CopilotStore`: RAG query history, token badges, citations, and quick suggestions.
    - `ProfileStore`: Profile view, token usage metrics, and personal data editing.
- **Corporate Design System:**
    - Fonts: *Ubuntu* and *Ubuntu Mono*.
    - Palette: Sky Blue (`#0284C7`), Mint Green (`#10B981`), Slate (`#0F172A`), White/Surface (`#FFFFFF` / `#F8FAFC`).
    - **Strict rectangular borders (`border-radius: 0px`):** Visual components have no rounded corners.
    - Responsive design for mobile phones, tablets, and desktop monitors.

# Technical and Architecture Decision Record (ADRs)

**Project:** Internal Messaging and AI Copilot Platform — Riwi Co.
**Author:** Santiago Munoz Nakamoto
**Repository:** `sanzmunoz/chat_consultas`
**Database:** PostgreSQL 15+ (`bd_santiago_munoz_nakamoto`)

---

## 1. Architecture Decision Records (ADRs)

### ADR-01: FastAPI + asyncpg (No ORM)
- **Context:** The platform needs high performance for asynchronous I/O, automatic interactive OpenAPI documentation (`/docs`), and strict transaction control. This control injects the session actor identity with `SET LOCAL app.current_user_id = '<actor_id>'` before each operation protected by Row Level Security (RLS).
- **Decision:** Use **FastAPI 0.115+** with Python 3.12 and the low-level asynchronous driver **asyncpg 0.30+**.
- **Consequences:**
  - Fine control over connection and transaction life cycles.
  - Direct execution of functions and stored procedures (`rw_fn_send_message`, `rw_sp_query_users`, `rw_sp_edit_or_delete_user`).
  - `statement_cache_size=0` is required in the pool to avoid prepared-statement cache mismatches in multiplexed sessions.
  - Automatic generation of OpenAPI 3.1 specifications and export to `docs/api-collection.json`.

---

### ADR-02: Clean Architecture (Hexagonal / Ports and Adapters)
- **Context:** Business rules must be fully separate from infrastructure details (PostgreSQL, OpenAI SDK, FastAPI, and hash libraries).
- **Decision:** Structure the backend in 4 strict layers. Dependencies point only toward the center:
  1. `domain/`: Pure `@dataclass` entities without external dependencies, plus ports defined with `typing.Protocol` (PEP 544).
  2. `application/`: Small use cases that coordinate business rules through interface injection.
  3. `infrastructure/`: Concrete adapters (`PgUserRepository`, `PgMessageRepository`, `OpenAILlmService`, `JwtService`).
  4. `presentation/`: FastAPI controllers, middleware (`CorrelationMiddleware`, `AuthMiddleware`), and Pydantic v2 schemas.
- **Consequences:** High testability, low coupling, and compliance with the Dependency Inversion Principle (DIP).

---

### ADR-03: Database Security with Row-Level Security (RLS) by Channel Membership
- **Context:** `project.txt` requires that no user can query, read, or infer messages or semantic context from channels where they are not a member.
- **Decision:**
  - Create the application role `rw_app_role` with the `NOBYPASSRLS` attribute.
  - Prohibit physical deletion (`REVOKE DELETE ON ALL OPERATIONAL TABLES`).
  - Use row-level security policies (`rw_pol_messages_select`, `rw_pol_messages_insert`, `rw_pol_messages_update`) based on `rw_is_channel_member(channel_id)` and the session identity from `rw_get_current_user_id()`.
- **Consequences:** The database engine enforces security. If an application query accidentally misses a filter, PostgreSQL blocks access in a predictable way.

---

### ADR-04: O(1) Keyset Pagination vs OFFSET Paging
- **Context:** In channels with thousands or millions of messages, `OFFSET N LIMIT M` has linear performance cost ($O(N)$). It can also create errors, such as duplicate or skipped messages, when new records arrive in real time.
- **Decision:** Implement deterministic cursor pagination with the compound tuple `(created_at, id)`.
- **Supporting query:**
  ```sql
  WHERE channel_id = $1 
    AND is_deleted = FALSE 
    AND ($2::TIMESTAMPTZ IS NULL OR (m.created_at, m.id) < ($2, $3::UUID))
  ORDER BY m.created_at DESC, m.id DESC
  LIMIT $4;
  ```
- **Optimized index:**
  ```sql
  CREATE INDEX rw_idx_messages_keyset ON rw_messages (channel_id, created_at DESC, id DESC) WHERE is_deleted = FALSE;
  ```
- **Consequences:** Read complexity stays at $O(1)$, regardless of the history depth.

---

### ADR-05: State Preservation and Soft Delete with a Partial Unique Index
- **Context:** Physical data deletion is forbidden to ensure complete audit records and forensic traceability. The original content must also remain available after an edit.
- **Decision:**
  - Edits: The `rw_fn_sync_message_search` trigger automatically saves the previous content in `original_content` during the first edit and updates `is_edited = TRUE` and `edited_at`.
  - Deletions: Set `is_deleted = TRUE` and `deleted_at = CURRENT_TIMESTAMP`.
  - Reference uniqueness: Use a partial index, `CREATE UNIQUE INDEX rw_idx_uq_active_msg_ref ON rw_messages (msg_ref) WHERE is_deleted = FALSE;`, so references from deleted messages can be reused without breaking integrity.
- **Consequences:** No loss of historical information and strict audit compliance.

---

### ADR-06: Interchangeable Artificial Intelligence Provider (LlmServicePort)
- **Context:** The AI Copilot needs RAG (Retrieval-Augmented Generation), while the provider must remain replaceable. The system may use OpenAI, Anthropic, Gemini, or local models without changing application code.
- **Decision:** Define the `LlmServicePort` contract in the domain layer. Implement `OpenAILlmService` in infrastructure with a deterministic offline *fallback*.
- **Consequences:** Automated tests and CI/CD environments run in isolation. They do not use external API quotas or fail because of network latency.

---

### ADR-07: Versioned System Prompt as External YAML
- **Context:** The AI Copilot behavior must be auditable, configurable, and versioned independently from the source code life cycle.
- **Decision:** Store the assistant configuration in `backend/prompts/v1.yaml`. It contains role instructions, scope limits, citation rules with brackets such as `[msg-XXXX]`, and clear refusal handling.
- **Consequences:** The model behavior can be changed or improved through declarative versions (`v2.yaml`, `v3.yaml`) without changing compilation or runtime logic.

---

### ADR-08: Angular 22 Standalone + NgRx Signal Store + Custom Design System
- **Context:** The frontend must provide a smooth, reactive real-time experience and follow the corporate identity: Ubuntu typography, the color palette (Sky Blue `#0284C7`, Mint Green `#10B981`, Slate `#0F172A`), and **strict rectangular borders with no rounding (`border-radius: 0px`)**.
- **Decision:**
  - Angular 22 with a 100% Standalone architecture (no `NgModule`).
  - State reactivity through `@ngrx/signals` (`ConversationStore`, `CopilotStore`, `ProfileStore`).
  - Functional interceptors to add the `X-Correlation-Id` header and automatically rotate the JWT after a 401 response.
  - Global CSS rule `* { border-radius: 0 !important; }` and custom semantic variables.
- **Consequences:** Declarative code, efficient rendering with Signals, and an exact corporate design.

---

## 2. Strict Application of SOLID Principles

| Principle | How It Appears in the Project |
|---|---|
| **S — Single Responsibility** | Each use case (`LoginUseCase`, `SendMessageUseCase`, `ListMessagesKeysetUseCase`, `QueryCopilotUseCase`) coordinates only one specific business operation. Repositories and controllers are decoupled. |
| **O — Open/Closed** | The AI service is open for extension and closed for modification through `LlmServicePort`. Adding `GeminiLlmService` does not require changes to existing use cases. |
| **L — Liskov Substitution** | Any class that implements `MessageRepositoryPort` or `UserRepositoryPort` can replace `PgMessageRepository` or `PgUserRepository` without changing expected behavior. |
| **I — Interface Segregation** | Ports are divided by bounded context (`UserRepositoryPort`, `ChannelRepositoryPort`, `MessageRepositoryPort`, `CopilotLogRepositoryPort`, `LlmServicePort`) instead of using large interfaces. |
| **D — Dependency Inversion** | High-level layers (`application`) depend on abstractions (`domain/ports`), while low-level layers (`infrastructure` and `presentation`) implement or use them through dependency injection. |

---

## 3. Database Decision Matrix

| Requirement | Implemented Solution | Technical Reason |
|---|---|---|
| Lexical Search | PostgreSQL FTS (`search_vector tsvector` + GIN) | Supports Spanish search with `websearch_to_tsquery`, relevance ranking with `ts_rank`, and match highlighting with `ts_headline`. |
| Semantic Search | `pgvector` (`vector(1536)` + HNSW index) | Calculates cosine similarity (`<=>`) in the database and speeds it up with hierarchical navigable small-world graphs (HNSW). |
| Access Isolation | Row-Level Security (`rw_app_role`) | Ensures that no user, even through accidental SQL injection, can query data from channels where they are not a member. |
| Referential Integrity | `ON DELETE RESTRICT` for core entities | Prevents accidental loss of history and conversations when users or channels are removed. |
| Secure Session | Refresh Token Rotation with SHA-256 | Each refresh token is used only once. Stored tokens are hashed, which prevents reuse if the database is compromised. |

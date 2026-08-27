# Arquitectura del Sistema: Plataforma de Mensajería y Copiloto IA

**Proyecto:** Riwi Co. Internal Messaging & AI Copilot Platform  
**Arquitectura:** Clean Architecture (Hexagonal / Ports & Adapters)  
**Base de Datos:** PostgreSQL 15+ (`bd_santiago_munoz_nakamoto`) con extensión `vector`  
**Frontend:** Angular 22 Standalone + NgRx Signal Store  
**Backend:** Python 3.12 + FastAPI + asyncpg  

---

## 1. Visión Global de la Arquitectura

```mermaid
graph TB
    subgraph CloudDeployment ["Infraestructura & Despliegue"]
        FE_HOST["Frontend: Vercel / Nginx (Container)"]
        BE_HOST["Backend: Render / FastAPI (Docker Multi-stage)"]
        DB_HOST["Base de Datos: PostgreSQL 16 + pgvector (Managed/Docker)"]
    end

    subgraph FrontendArchitecture ["Frontend: Angular 22 Standalone"]
        UI_Z1["Zona 1: Conversación & Mensajería"]
        UI_Z2["Zona 2: Copiloto IA & RAG"]
        UI_Z3["Zona 3: Perfil & Auditoría"]
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

        subgraph ApplicationLayer ["2. Application Layer (Casos de Uso)"]
            UC_AUTH["Auth: Login, RefreshToken"]
            UC_MSG["Messages: Keyset Listing, Send, Search, Edit, Delete"]
            UC_USER["Users: QueryUsers, EditDeleteUser (SP)"]
            UC_COP["Copilot: QueryCopilot (RAG), GetUsage"]
        end

        subgraph DomainLayer ["3. Domain Layer (Núcleo Puro)"]
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

    subgraph DatabaseLayer ["Base de Datos: PostgreSQL 16 + pgvector"]
        RLS_POL["Row-Level Security (rw_app_role NOBYPASSRLS)"]
        PROC_FN["Funciones & Procedimientos: rw_fn_send_message, rw_sp_query_users, rw_sp_edit_or_delete_user"]
        FTS_TRG["FTS: tsvector + GIN Trigger en español"]
        VEC_IDX["Vector: 1536-dim HNSW Index (Cosine Distance)"]
        TABLES["7 Tablas rw_*: users, channels, channel_members, messages, read_receipts, copilot_logs, refresh_tokens"]
    end

    %% Conexiones Frontend -> Backend
    UI_Z1 --> NGRX_S
    UI_Z2 --> NGRX_S
    UI_Z3 --> NGRX_S
    NGRX_S --> CORE_SVC
    CORE_SVC --> INTERCEPTORS
    INTERCEPTORS -- "HTTPS REST + JWT Bearer" --> ROUTERS

    %% Flujo interno Backend
    ROUTERS --> UC_AUTH & UC_MSG & UC_USER & UC_COP
    UC_AUTH & UC_MSG & UC_USER & UC_COP --> PORTS
    ENTITIES --- PORTS
    REPO_PG -.->|Implements| PORTS
    LLM_SVC -.->|Implements| PORTS
    REPO_PG --> SEC_PG
    SEC_PG -- "SET LOCAL + SQL" --> DatabaseLayer
```

---

## 2. Diagrama de Secuencia: Flujo RAG del Copiloto IA con Seguridad RLS

```mermaid
sequenceDiagram
    autonumber
    actor Usuario as Usuario Riwi
    participant FE as Angular Copilot (Zona 2)
    participant API as FastAPI Router (/api/copilot/query)
    participant Pool as asyncpg Pool (Actor Context)
    participant DB as PostgreSQL (pgvector + RLS)
    participant LLM as OpenAI LLM Service / Fallback

    Usuario->>FE: Ingresa consulta en lenguaje natural
    FE->>API: POST /api/copilot/query (Bearer JWT)
    API->>API: Extrae y valida actor_id desde JWT
    API->>LLM: Genera embedding para la consulta (text-embedding-3-small)
    LLM-->>API: Vector flotante de 1536 dimensiones
    API->>Pool: get_connection_with_actor(actor_id)
    Pool->>DB: BEGIN TRANSACTION + SET LOCAL app.current_user_id = '<actor_id>'
    API->>DB: SELECT con distancia coseno (<=>) filtrando rw_is_channel_member(channel_id)
    Note over DB: PostgreSQL ejecuta la búsqueda vectorial ÚNICAMENTE sobre mensajes<br/>de canales donde el usuario autenticado tiene membresía activa.
    DB-->>API: Mensajes relevantes contextualizados con [msg-XXXX]
    
    alt Contexto disponible en canales autorizados
        API->>LLM: Carga prompts/v1.yaml + Mensajes autorizados + Pregunta
        LLM-->>API: Respuesta generada con citas estructuradas
    else Sin mensajes autorizados o canal ajeno
        API->>LLM: Carga prompts/v1.yaml + Contexto vacío
        LLM-->>API: Negativa transparente: "No tengo acceso a información sobre ese tema..."
    end

    API->>DB: INSERT INTO rw_copilot_logs (tokens, modelo, query, response)
    API->>Pool: COMMIT TRANSACTION
    API-->>FE: 200 OK (answer, citations, model, tokens_used)
    FE-->>Usuario: Renderiza respuesta interactiva con tarjetas de citas clicables
```

---

## 3. Modelo de Datos Relacional (Normalización 3FN)

El modelo está compuesto por 7 tablas normalizadas en Tercera Forma Normal (3FN), todas bajo el prefijo obligatorio `rw_`:

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

## 4. Estrategia de Seguridad y Aislamiento

1. **Rol de Base de Datos sin Privilegios de Superusuario:**
   - Rol `rw_app_role` creado con la cláusula `NOBYPASSRLS`.
   - Se revocan permisos de `DELETE` físico sobre todas las tablas operacionales.
2. **Propagación del Actor:**
   - Cada solicitud HTTP autenticada extrae el `user_id` del token JWT verificado en el backend.
   - Antes de ejecutar cualquier consulta, el pool de `asyncpg` ejecuta `SET LOCAL app.current_user_id = '<actor_id>'` dentro de una transacción.
3. **Funciones de Seguridad RLS:**
   - `rw_is_channel_member(p_channel_id)`: Comprueba en $O(1)$ la membresía del usuario actual en el canal solicitado.
   - Las políticas RLS aplican automáticamente a `SELECT`, `INSERT` y `UPDATE`.

---

## 5. Diseño del Frontend (Angular 22 Standalone)

- **NgRx Signal Stores:** Gestión de estado predecible y reactiva con Signals de Angular:
  - `ConversationStore`: Canales activos, paginación keyset diferida, estados de envío (`pending`, `sent`, `failed`), búsqueda FTS.
  - `CopilotStore`: Historial de consultas RAG, badges de tokens, citas y sugerencias rápidas.
  - `ProfileStore`: Visualización de perfil, métricas de consumo de tokens y edición de datos personales.
- **Sistema de Diseño Corporativo:**
  - Tipografía: *Ubuntu* y *Ubuntu Mono*.
  - Paleta: Azul Cielo (`#0284C7`), Verde Menta (`#10B981`), Pizarra (`#0F172A`), Fondo Blanco/Superficie (`#FFFFFF` / `#F8FAFC`).
  - **Bordes Rectangulares Estrictos (`border-radius: 0px`):** Componentes visuales sin esquinas redondeadas.
  - Diseño responsivo adaptativo con soporte para móviles, tablets y monitores de escritorio.

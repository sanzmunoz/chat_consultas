# Arquitectura del Sistema: Clean Architecture & Decisiones Técnicas

**Proyecto:** Riwi Co. Messaging & AI Copilot Platform  
**Patrón:** Clean Architecture (Arquitectura Limpia / Puertos y Adaptadores)

---

## 1. Estructura de Capas

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  - FastAPI Routers: Auth, Channels, Messages, Users, Copilot│
│  - Pydantic v2 Schemas (Validation & Serialization)         │
│  - Middleware: Correlation ID, Auth (JWT), Global Exceptions│
└──────────────────────────────┬──────────────────────────────┘
                               │ Calls Use Cases
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                       │
│  - Use Cases: LoginUseCase, SendMessageUseCase,             │
│    ListMessagesKeysetUseCase, QueryCopilotUseCase, etc.     │
│  - Orquestación de lógica de negocio pura                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Depends on Ports (Interfaces)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                          │
│  - Entities: User, Channel, Message, CopilotLog             │
│  - Ports (Protocols): UserRepositoryPort,                   │
│    ChannelRepositoryPort, MessageRepositoryPort,            │
│    CopilotLogRepositoryPort, LlmServicePort                 │
└──────────────────────────────▲──────────────────────────────┘
                               │ Implemented by
┌──────────────────────────────┴──────────────────────────────┐
│                    INFRASTRUCTURE LAYER                     │
│  - Database: asyncpg Pool, PostgreSQL RLS, pgvector         │
│  - Repositories: PgUserRepository, PgMessageRepository, etc.│
│  - Security: JWT Service (PyJWT), Hasher (bcrypt)           │
│  - External AI: OpenAILlmService (OpenAI Python SDK)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Decisión Técnica: Keyset Pagination vs Offset Pagination

### Problema con OFFSET:
En aplicaciones de mensajería en tiempo real con millones de filas, `OFFSET N LIMIT M` presenta una complejidad temporal $O(N)$, provocando escaneo completo de páginas descartadas y anomalías de datos (mensajes duplicados o saltados al insertar nuevos registros).

### Solución Keyset Pagination (O(1)):
Se utiliza una tupla determinista indexada por `(created_at, id)`:

```sql
SELECT id, msg_ref, channel_id, author_id, content, created_at
FROM rw_messages
WHERE channel_id = $1
  AND is_deleted = FALSE
  AND ($2::timestamptz IS NULL OR (created_at, id) < ($2, $3))
ORDER BY created_at DESC, id DESC
LIMIT $4;
```

**Índice de soporte optimizado:**
```sql
CREATE INDEX rw_idx_messages_keyset ON rw_messages (channel_id, created_at DESC, id DESC);
```

---

## 3. Principios SOLID Aplicados

- **S (Single Responsibility):** Cada caso de uso tiene una única razón para cambiar.
- **O (Open/Closed):** Para agregar un nuevo proveedor de modelos LLM (e.g. Claude o Gemini), basta con implementar `LlmServicePort` sin tocar la capa de aplicación.
- **L (Liskov Substitution):** Cualquier clase que implemente `MessageRepositoryPort` puede sustituir a `PgMessageRepository`.
- **I (Interface Segregation):** Puertos específicos y compactos por entidad.
- **D (Dependency Inversion):** Los casos de uso dependen exclusivamente de protocolos abstractos, nunca de implementaciones concretas de base de datos o librerías externas.

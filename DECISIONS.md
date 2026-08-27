# Registro de Decisiones Técnicas y de Arquitectura (ADRs)

**Proyecto:** Plataforma de Mensajería Interna y Copiloto IA — Riwi Co.  
**Autor:** Santiago Muñoz Nakamoto  
**Repositorio:** `sanzmunoz/chat_consultas`  
**Base de Datos:** PostgreSQL 15+ (`bd_santiago_munoz_nakamoto`)

---

## 1. Registro de Decisiones de Arquitectura (ADRs)

### ADR-01: FastAPI + asyncpg (Sin ORM)
- **Contexto:** La plataforma requiere alto rendimiento en I/O asíncrono, documentación interactiva OpenAPI automática (`/docs`), y control transaccional estricto para inyectar la identidad del actor de sesión mediante `SET LOCAL app.current_user_id = '<actor_id>'` antes de cada operación sensible sujeta a Row Level Security (RLS).
- **Decisión:** Usar **FastAPI 0.115+** con Python 3.12 y el driver asíncrono de bajo nivel **asyncpg 0.30+**.
- **Consecuencias:**
  - Control granular sobre el ciclo de vida de conexiones y transacciones.
  - Ejecución directa de funciones y procedimientos almacenados (`rw_fn_send_message`, `rw_sp_query_users`, `rw_sp_edit_or_delete_user`).
  - Configuración mandatoria de `statement_cache_size=0` en el pool para evitar desalineaciones de caché de sentencias preparadas en sesiones multiplexadas.
  - Generación automática de especificaciones OpenAPI 3.1 y exportación a `docs/api-collection.json`.

---

### ADR-02: Clean Architecture (Hexagonal / Puertos y Adaptadores)
- **Contexto:** Se requiere desacoplar por completo las reglas del negocio de los detalles de infraestructura (PostgreSQL, OpenAI SDK, FastAPI, librerías de hash).
- **Decisión:** Estructurar el backend en 4 capas estrictas con la regla de dependencia apuntando exclusivamente hacia el centro:
  1. `domain/`: Entidades puras en `@dataclass` sin dependencias externas + Puertos definidos con `typing.Protocol` (PEP 544).
  2. `application/`: Casos de uso atómicos orquestando reglas de negocio con inyección de interfaces.
  3. `infrastructure/`: Adaptadores concretos (`PgUserRepository`, `PgMessageRepository`, `OpenAILlmService`, `JwtService`).
  4. `presentation/`: Controladores FastAPI, middlewares (`CorrelationMiddleware`, `AuthMiddleware`), schemas Pydantic v2.
- **Consecuencias:** Máxima testabilidad, bajo acoplamiento y cumplimiento del principio de Inversión de Dependencias (DIP).

---

### ADR-03: Seguridad en Base de Datos vía Row-Level Security (RLS) por Membresía de Canal
- **Contexto:** `project.txt` exige que ningún usuario pueda consultar, leer o inferir mensajes o contextos semánticos de canales a los que no pertenece.
- **Decisión:**
  - Creación del rol de aplicación `rw_app_role` con atributo `NOBYPASSRLS`.
  - Prohibición de borrado físico (`REVOKE DELETE ON ALL OPERATIONAL TABLES`).
  - Políticas de seguridad a nivel de fila (`rw_pol_messages_select`, `rw_pol_messages_insert`, `rw_pol_messages_update`) basadas en la función de verificación `rw_is_channel_member(channel_id)` y la identidad de sesión `rw_get_current_user_id()`.
- **Consecuencias:** La seguridad se delega al motor de base de datos. Si una consulta omite accidentalmente un filtro en la capa de aplicación, PostgreSQL bloquea el acceso de manera determinista.

---

### ADR-04: Paginación Keyset O(1) vs OFFSET Paging
- **Contexto:** En canales de mensajería con miles o millones de mensajes, `OFFSET N LIMIT M` degrada linealmente el rendimiento ($O(N)$) y genera desalineaciones (mensajes duplicados o saltados) cuando entran nuevos registros en tiempo real.
- **Decisión:** Implementar paginación determinista por cursor Keyset basada en la tupla compuesta `(created_at, id)`.
- **Query de soporte:**
  ```sql
  WHERE channel_id = $1 
    AND is_deleted = FALSE 
    AND ($2::TIMESTAMPTZ IS NULL OR (m.created_at, m.id) < ($2, $3::UUID))
  ORDER BY m.created_at DESC, m.id DESC
  LIMIT $4;
  ```
- **Índice optimizado:**
  ```sql
  CREATE INDEX rw_idx_messages_keyset ON rw_messages (channel_id, created_at DESC, id DESC) WHERE is_deleted = FALSE;
  ```
- **Consecuencias:** Complejidad de lectura constante $O(1)$ sin importar la profundidad del historial.

---

### ADR-05: Preservación de Estado y Soft-Delete con Índice Único Parcial
- **Contexto:** Está prohibido el borrado físico de datos para garantizar auditoría completa y trazabilidad forense. Asimismo, se debe conocer el contenido original ante ediciones.
- **Decisión:**
  - Modificaciones: Trigger `rw_fn_sync_message_search` captura automáticamente el contenido previo en `original_content` durante la primera edición y actualiza `is_edited = TRUE` y `edited_at`.
  - Eliminaciones: Marcar `is_deleted = TRUE` y `deleted_at = CURRENT_TIMESTAMP`.
  - Unicidad de referencias: Se emplea un índice parcial `CREATE UNIQUE INDEX rw_idx_uq_active_msg_ref ON rw_messages (msg_ref) WHERE is_deleted = FALSE;` para que referencias de mensajes borrados puedan ser reutilizadas sin violar integridad.
- **Consecuencias:** Cero pérdida de información histórica con cumplimiento estricto de auditoría.

---

### ADR-06: Proveedor de Inteligencia Artificial Intercambiable (LlmServicePort)
- **Contexto:** Se requiere integrar capacidades de RAG (Retrieval-Augmented Generation) para el Copiloto IA manteniendo la capacidad de cambiar de proveedor (OpenAI, Anthropic, Gemini, o modelos locales) sin modificar el código de aplicación.
- **Decisión:** Definir el contrato `LlmServicePort` en la capa de dominio e implementar `OpenAILlmService` en infraestructura con un mecanismo de *fallback determinista* offline.
- **Consecuencias:** Las pruebas automatizadas y entornos CI/CD se ejecutan de manera aislada sin consumir cuotas externas de API ni fallar por latencia de red.

---

### ADR-07: System Prompt Versionado como YAML Externo
- **Contexto:** El comportamiento del Copiloto IA debe ser auditable, configurable y versionable independientemente del ciclo de vida del código fuente.
- **Decisión:** Ubicar la configuración del asistente en `backend/prompts/v1.yaml`, estructurando instrucciones de rol, restricciones de alcance, directrices de citas entre corchetes `[msg-XXXX]` y manejo de negativas transparentes.
- **Consecuencias:** Cambiar o afinar el comportamiento del modelo se realiza mediante versionamiento declarativo (`v2.yaml`, `v3.yaml`) sin alterar lógica de compilación o ejecución.

---

### ADR-08: Angular 22 Standalone + NgRx Signal Store + Custom Design System
- **Contexto:** El frontend debe ofrecer una experiencia fluida y reactiva en tiempo real, cumpliendo con la identidad corporativa: tipografía Ubuntu, paleta de colores (Azul Cielo `#0284C7`, Verde Menta `#10B981`, Pizarra `#0F172A`), y **bordes rectangulares estrictos sin redondeo (`border-radius: 0px`)**.
- **Decisión:**
  - Angular 22 con arquitectura 100% Standalone (sin `NgModule`).
  - Reactividad de estado mediante `@ngrx/signals` (`ConversationStore`, `CopilotStore`, `ProfileStore`).
  - Interceptores funcionales para inyección de encabezado `X-Correlation-Id` y rotación automática de JWT en 401.
  - Regla global CSS `* { border-radius: 0 !important; }` y variables semánticas personalizadas.
- **Consecuencias:** Código declarativo, renderizado eficiente con Signals y diseño corporativo exacto.

---

## 2. Aplicación Rigurosa de Principios SOLID

| Principio | Manifestación en el Proyecto |
|---|---|
| **S — Single Responsibility** | Cada caso de uso (`LoginUseCase`, `SendMessageUseCase`, `ListMessagesKeysetUseCase`, `QueryCopilotUseCase`) orquesta exclusivamente una operación de negocio específica. Repositorios y controladores están desacoplados. |
| **O — Open/Closed** | El servicio de IA está abierto a extensión y cerrado a modificación mediante la interfaz `LlmServicePort`. Añadir un `GeminiLlmService` no requiere modificar ningún caso de uso existente. |
| **L — Liskov Substitution** | Cualquier clase que implemente `MessageRepositoryPort` o `UserRepositoryPort` puede sustituir a los adaptadores `PgMessageRepository` y `PgUserRepository` sin alterar el comportamiento esperado del sistema. |
| **I — Interface Segregation** | Los puertos están estrictamente divididos por contexto delimitado (`UserRepositoryPort`, `ChannelRepositoryPort`, `MessageRepositoryPort`, `CopilotLogRepositoryPort`, `LlmServicePort`) evitando interfaces monolíticas. |
| **D — Dependency Inversion** | Las capas de alto nivel (`application`) dependen de abstracciones (`domain/ports`), y las capas de bajo nivel (`infrastructure` y `presentation`) implementan o consumen dichas abstracciones mediante inyección de dependencias. |

---

## 3. Matriz de Decisiones de Base de Datos

| Requisito | Solución Implementada | Justificación Técnica |
|---|---|---|
| Búsqueda Léxica | PostgreSQL FTS (`search_vector tsvector` + GIN) | Permite búsqueda en español con `websearch_to_tsquery`, ranking por relevancia `ts_rank` y resaltado de coincidencias con `ts_headline`. |
| Búsqueda Semántica | `pgvector` (`vector(1536)` + índice HNSW) | Permite cálculo de similitud coseno (`<=>`) a nivel de base de datos acelerado por grafos navegables de mundos pequeños jerárquicos (HNSW). |
| Aislamiento de Acceso | Row-Level Security (`rw_app_role`) | Garantiza que ningún usuario, ni siquiera mediante inyección SQL accidental, pueda consultar datos de canales donde no es miembro. |
| Integridad Referencial | `ON DELETE RESTRICT` en entidades core | Evita la pérdida accidental de historial y conversaciones ante eliminación de usuarios o canales. |
| Sesión Segura | Refresh Token Rotation con SHA-256 | El token de actualización solo se usa una vez; los tokens almacenados se guardan hasheados impidiendo reutilización en caso de compromiso de base de datos. |

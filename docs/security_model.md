# Modelo de Seguridad y Row Level Security (RLS)

**Proyecto:** Riwi Co. Messaging & AI Copilot Platform  
**Base de Datos:** `bd_santiago_munoz_nakamoto`  
**Motor:** PostgreSQL 16 con extensión `pgvector`

---

## 1. Principio Fundamental: Membresía Explícita por Canal

A diferencia de modelos basados en jerarquías rígidas (donde un rol superior tiene acceso irrestricto a todas las conversaciones), la plataforma Riwi implementa un **modelo de seguridad basado estrictamente en membresía de canal** (`rw_channel_members`).

Un usuario (incluso un administrador del sistema) solo tiene visibilidad de lectura y escritura sobre aquellos canales donde ha sido expresamente registrado como miembro.

```
                  ┌───────────────────────────────┐
                  │    JWT Bearer Authentication  │
                  └───────────────┬───────────────┘
                                  │ Claims: sub (UUID), role
                                  ▼
                  ┌───────────────────────────────┐
                  │  SET LOCAL app.current_user_id│
                  └───────────────┬───────────────┘
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
┌──────────────────────────────┐            ┌──────────────────────────────┐
│       rw_messages (RLS)      │            │     rw_copilot_logs (RLS)    │
│  rw_is_channel_member() = T  │            │     user_id = actor_id       │
└──────────────────────────────┘            └──────────────────────────────┘
```

---

## 2. Configuración del Rol de Aplicación (`rw_app_role`)

Para garantizar que el motor de PostgreSQL aplique de forma obligatoria las políticas de RLS, la conexión del backend se ejecuta bajo el rol `rw_app_role`, el cual fue configurado con la directiva explícita `NOBYPASSRLS`:

```sql
CREATE ROLE rw_app_role WITH LOGIN PASSWORD 'rw_app_secure_pass_2026' NOBYPASSRLS;
```

---

## 3. Propagación Segura del Actor (`app.current_user_id`)

Cada transacción que interactúa con la base de datos establece una variable de sesión local `app.current_user_id` mediante el context manager `get_connection_with_actor`:

```python
async with get_connection_with_actor(actor_id) as conn:
    # Dentro de esta transacción:
    # rw_get_current_user_id() = actor_id
```

### Funciones de Seguridad en Base de Datos

1. `rw_get_current_user_id()`: Extrae el UUID del actor actual de la variable `app.current_user_id`.
2. `rw_is_channel_member(p_channel_id, p_user_id)`: Valida en tiempo constante si el actor pertenece al canal.
3. `rw_is_admin(p_user_id)`: Comprueba si el usuario posee rol administrativo.

---

## 4. Políticas RLS Activas

### 4.1. Mensajes (`rw_messages`)
- **SELECT:** `rw_is_channel_member(channel_id, rw_get_current_user_id()) AND is_deleted = FALSE`
- **INSERT:** `rw_is_channel_member(channel_id, rw_get_current_user_id()) AND author_id = rw_get_current_user_id()`
- **UPDATE:** `author_id = rw_get_current_user_id() OR rw_is_admin(rw_get_current_user_id())`

### 4.2. Canales (`rw_channels`)
- **SELECT:** `rw_is_channel_member(id, rw_get_current_user_id())`

### 4.3. Miembros de Canal (`rw_channel_members`)
- **SELECT:** `rw_is_channel_member(channel_id, rw_get_current_user_id())`

---

## 5. Inmutabilidad y Auditoría de Mensajes

1. **Eliminación Física Prohibida:** Los mensajes nunca se eliminan físicamente (`DELETE`). Toda eliminación es lógica mediante `is_deleted = TRUE` y registro de `deleted_at`.
2. **Edición con Preservación Histórica:** La primera edición de un mensaje almacena el texto inicial en la columna `original_content` y marca `is_edited = TRUE`.
3. **Rotación de Refresh Tokens:** Los tokens de refresco son de un solo uso. Cualquier intento de reutilizar un token revocado es rechazado de inmediato.

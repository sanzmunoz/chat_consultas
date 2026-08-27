# Riwi Co. — Internal Messaging Platform & AI Copilot (RAG)

> **Plataforma Integral de Comunicación Interna y Copiloto IA con Arquitectura Limpia, PostgreSQL Row Level Security (RLS), Paginación por Keyset y Frontend Angular 22.**

---

## 📋 Resumen del Proyecto

Este repositorio contiene la solución completa para el sistema de mensajería empresarial y búsqueda semántica con IA de **Riwi Co.**, diseñado para garantizar el aislamiento estricto de información por canal, alto rendimiento transaccional y asistencia inteligente transparente.

### 🌟 Características Principales

1. **Seguridad Basada en Membresía de Canal (RLS):**
   - Políticas PostgreSQL nativas con `NOBYPASSRLS`.
   - Propagación de identidad del actor mediante `app.current_user_id`.
   - Aislamiento absoluto entre canales públicos y privados.
2. **Copiloto IA RAG Scoped con Citas y Negativas Transparentes:**
   - Vectorización con `text-embedding-3-small` e índice HNSW (`pgvector`).
   - Generación con OpenAI `gpt-4o-mini` y versión de prompt `v1.yaml`.
   - Citas verificables (`[msg-xxxx]`) y auditoría de tokens en `rw_copilot_logs`.
3. **Paginación Keyset Indexada de Alta Eficiencia ($O(1)$):**
   - Sin uso de `OFFSET` para navegación fluida en grandes volúmenes de datos.
4. **Búsqueda Léxica Full-Text con Resaltado:**
   - Motor `tsvector`/`tsquery` en español con fragmentación y resaltado (`ts_headline`).
5. **Frontend Moderno Angular 22:**
   - Standalone Components + NgRx Signal Store + Angular Material.
   - 3 Zonas integradas: Conversación, Copiloto RAG y Perfil con Métricas de Tokens.
   - Internacionalización i18n completa (Español / Inglés).
   - Estilo gráfico sharp: bordes rectangulares sin redondeo (`0px`), fuente Ubuntu, paleta Azul Claro (`#38BDF8`) y Verde Menta (`#10B981`).

---

## 🏗️ Arquitectura del Sistema

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

## 👥 Usuarios de Prueba (Seed Data)

Todos los usuarios cuentan con la contraseña por defecto: `riwi2026!`

| Usuario | Nombre Completo | Correo Corporativo | Rol Sistema | Cargo | Canales Asignados |
|---|---|---|---|---|---|
| `smunoz` | Santiago Muñoz | `santiago.munoz@riwi.co` | `admin` | Tech Lead & Architect | `#general`, `#backend-dev`, `#devops-infra` |
| `crojas` | Camila Rojas | `camila.rojas@riwi.co` | `member` | Senior Frontend Developer | `#general`, `#frontend-design` |
| `nvega` | Néstor Vega | `nestor.vega@riwi.co` | `member` | Backend Developer | `#general`, `#backend-dev` |
| `vcastro` | Valentina Castro | `valentina.castro@riwi.co` | `member` | QA Engineer | `#general`, `#frontend-design` |
| `alopez` | Andrés López | `andres.lopez@riwi.co` | `member` | DevOps Engineer | `#general`, `#devops-infra` |

---

## 🚀 Inicio Rápido (Docker Compose)

### 1. Clonar el repositorio y configurar variables de entorno:
```bash
cp .env.example .env
```

### 2. Levantar la plataforma completa:
```bash
docker compose up --build -d
```

### 3. Accesos:
- **Frontend SPA:** [http://localhost:4200](http://localhost:4200)
- **Backend API Docs (Swagger):** [http://localhost:4000/docs](http://localhost:4000/docs)
- **Backend ReDoc:** [http://localhost:4000/redoc](http://localhost:4000/redoc)

---

## 🧪 Ejecución de Pruebas de Validación por Fase

### Fase 1: Validación Base de Datos (SQL, RLS, Procedures, Consultas 1-4)
```bash
python3 scripts/test_phase1_validation.py
```
*Reporte de evidencias:* `docs/phase1_validation.md` (16/16 pruebas superadas).

### Fase 2: Validación Backend FastAPI & Seguridad RLS
```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests -v
```
*Reporte de evidencias:* `docs/phase2_validation.md` (9/9 pruebas superadas).

### Fase 3: Validación Frontend Angular & Unit Specs
```bash
cd frontend
npx ng test --no-watch
```
*Reporte de evidencias:* `docs/phase3_validation.md` (5/5 specs superadas).

### Fase 4: Prueba de Integración End-to-End
```bash
python3 scripts/test_phase4_e2e.py
```
*Reporte de evidencias:* `docs/phase4_validation.md`.

---

## 📂 Estructura del Repositorio

```
chat_consultas_riwi/
├── backend/                  # API REST FastAPI (Clean Architecture)
│   ├── prompts/v1.yaml       # System prompt versionado del copiloto
│   ├── src/
│   │   ├── domain/           # Entidades y Puertos (Protocols)
│   │   ├── application/      # Casos de uso
│   │   ├── infrastructure/   # Repositorios asyncpg, JWT, Hasher, OpenAI
│   │   └── presentation/     # Routers, Schemas Pydantic y Middleware
│   └── tests/                # Suite de pruebas automatizadas pytest
├── frontend/                 # SPA Angular 22 (Standalone + Signal Store)
│   ├── public/assets/i18n/   # Diccionarios de internacionalización (ES / EN)
│   └── src/app/
│       ├── core/             # Servicios, interceptores, guards y modelos
│       ├── features/         # Conversación, Copiloto RAG y Perfil
│       └── shared/           # Navbar, loading states y pipes
├── sql/                      # Scripts DDL, RLS, Funciones, Consultas y Seeds
│   ├── 01_schema.sql         # DDL con prefijo rw_ y extensiones
│   ├── 02_security_rls.sql   # Políticas de Row Level Security
│   ├── 03_functions_procedures.sql # Lógica atómica y procedimientos
│   ├── 04_queries.sql        # 4 Consultas SQL obligatorias
│   └── 05_seed.sql           # Datos iniciales idempotentes
├── docs/                     # Documentación técnica formal y reportes
│   ├── normalization.md      # Normalización 0FN -> 3FN y dependencias
│   ├── MER.png               # Diagrama Entidad-Relación de alta resolución
│   ├── security_model.md     # Documentación de seguridad y RLS
│   ├── copilot_rag.md        # Documentación de IA y políticas de contexto
│   ├── architecture.md       # Decisiones de diseño y arquitectura limpia
│   └── phase[1-4]_validation.md # Reportes de validación de cada fase
├── scripts/                  # Scripts utilitarios y suites de prueba
├── docker-compose.yml        # Orquestación de contenedores
├── .github/workflows/ci.yml  # Pipeline de CI/CD automatizado
└── README.md                 # Documentación general del proyecto
```

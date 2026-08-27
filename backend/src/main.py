import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.database.pool import init_db_pool, close_db_pool
from src.presentation.middleware.correlation_middleware import CorrelationMiddleware
from src.presentation.middleware.error_handler import global_exception_handler
from src.presentation.routers.auth_router import router as auth_router
from src.presentation.routers.channels_router import router as channels_router
from src.presentation.routers.messages_router import router as messages_router
from src.presentation.routers.users_router import router as users_router
from src.presentation.routers.copilot_router import router as copilot_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database pool
    try:
        await init_db_pool()
        print("✓ Database pool connected to PostgreSQL.")
    except Exception as e:
        print(f"⚠ Warning: Could not connect database pool on startup: {e}")
    yield
    # Shutdown: close database pool
    await close_db_pool()
    print("✓ Database pool closed.")

app = FastAPI(
    title="Riwi Co. Messaging & AI Copilot Platform API",
    description=(
        "Backend REST API con Clean Architecture, PostgreSQL Row Level Security (RLS), "
        "paginación por Keyset, búsqueda léxica y Copiloto RAG basado en OpenAI SDK."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 1. CORS Configuration
CLIENT_URL = os.getenv("CLIENT_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_URL] if CLIENT_URL != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-Id"]
)

# 2. Correlation ID Middleware
app.add_middleware(CorrelationMiddleware)

# 3. Global Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# 4. Include Routers
app.include_router(auth_router)
app.include_router(channels_router)
app.include_router(messages_router)
app.include_router(users_router)
app.include_router(copilot_router)

@app.get("/health", tags=["Salud del Sistema"], summary="Estado del servicio")
async def health_check():
    return {
        "status": "healthy",
        "service": "riwi-chat-backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=4000, reload=True)

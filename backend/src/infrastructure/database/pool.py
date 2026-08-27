import os
import asyncpg
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

_pool: Optional[asyncpg.Pool] = None

DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "bd_santiago_munoz_nakamoto")
DB_USER = os.getenv("DB_USER", "rw_app_role")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rw_app_secure_pass_2026")
DB_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
DB_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
DB_SSL = os.getenv("DB_SSL", "").lower() in ("true", "require", "1")

async def init_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if DATABASE_URL:
            # Render and Heroku use postgres:// instead of postgresql://
            dsn = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            ssl_option = "require" if DB_SSL or "render.com" in dsn or "supabase" in dsn or "neon.tech" in dsn else None
            _pool = await asyncpg.create_pool(
                dsn=dsn,
                ssl=ssl_option,
                min_size=DB_MIN_SIZE,
                max_size=DB_MAX_SIZE,
                statement_cache_size=0  # Required for dynamic SET LOCAL and RLS consistency
            )
        else:
            _pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                ssl="require" if DB_SSL else None,
                min_size=DB_MIN_SIZE,
                max_size=DB_MAX_SIZE,
                statement_cache_size=0  # Required for dynamic SET LOCAL and RLS consistency
            )
    return _pool

async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized. Call init_db_pool() first.")
    return _pool

@asynccontextmanager
async def get_connection_with_actor(actor_id: Optional[UUID] = None) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Context manager that acquires a connection, begins a transaction,
    and sets the session actor with SET LOCAL app.current_user_id.
    Guarantees isolation and propagates actor identity to PostgreSQL RLS policies.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if actor_id:
                await conn.execute(f"SET LOCAL app.current_user_id = '{actor_id}';")
            yield conn

import os
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.infrastructure.database.pool import init_db_pool, close_db_pool

# Configure test environment
os.environ["DB_HOST"] = os.getenv("DB_HOST", "localhost")
os.environ["DB_PORT"] = os.getenv("DB_PORT", "5433")
os.environ["DB_NAME"] = os.getenv("DB_NAME", "bd_santiago_munoz_nakamoto")
os.environ["DB_USER"] = os.getenv("DB_USER", "rw_app_role")
os.environ["DB_PASSWORD"] = os.getenv("DB_PASSWORD", "rw_app_secure_pass_2026")

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    await init_db_pool()
    yield
    await close_db_pool()

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def santiago_token(client: AsyncClient):
    """Admin token (Santiago Muñoz)"""
    resp = await client.post("/api/auth/login", json={
        "username_or_email": "smunoz",
        "password": "riwi2026!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest_asyncio.fixture
async def camila_token(client: AsyncClient):
    """Member token (Camila Rojas - #general, #frontend-design)"""
    resp = await client.post("/api/auth/login", json={
        "username_or_email": "crojas",
        "password": "riwi2026!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest_asyncio.fixture
async def nestor_token(client: AsyncClient):
    """Member token (Néstor Vega - #general, #backend-dev)"""
    resp = await client.post("/api/auth/login", json={
        "username_or_email": "nvega",
        "password": "riwi2026!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

@pytest_asyncio.fixture
async def valentina_token(client: AsyncClient):
    """Member token (Valentina Castro - #general, #frontend-design)"""
    resp = await client.post("/api/auth/login", json={
        "username_or_email": "vcastro",
        "password": "riwi2026!"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]

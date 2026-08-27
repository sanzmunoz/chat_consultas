# Multi-stage Dockerfile for FastAPI Backend
# Stage 1: Build stage with compiler tools
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir --prefix=/install \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    asyncpg>=0.30.0 \
    pgvector>=0.3.0 \
    pydantic>=2.9.0 \
    pydantic-settings>=2.4.0 \
    pyjwt>=2.9.0 \
    passlib[bcrypt]>=1.7.4 \
    bcrypt>=4.2.0 \
    openai>=1.40.0 \
    pyyaml>=6.0.0 \
    python-multipart>=0.0.9 \
    numpy>=1.26.0

# Stage 2: Final lightweight runtime
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source and prompt files
COPY src/ ./src/
COPY prompts/ ./prompts/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 4000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "4000"]


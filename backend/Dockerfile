FROM python:3.12-slim

WORKDIR /app

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    asyncpg>=0.29.0 \
    pgvector>=0.3.0 \
    pydantic>=2.8.0 \
    pydantic-settings>=2.4.0 \
    pyjwt>=2.9.0 \
    bcrypt>=4.2.0 \
    openai>=1.40.0 \
    pyyaml>=6.0.0 \
    numpy>=1.26.0

# Copy application source and prompts
COPY src/ ./src/
COPY prompts/ ./prompts/

EXPOSE 4000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "4000"]

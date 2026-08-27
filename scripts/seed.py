#!/usr/bin/env python3
"""
Seed script for Riwi Co. Messaging Platform (bd_santiago_munoz_nakamoto).
Loads schema and normalized seed into PostgreSQL database.
"""
import os
import sys
import asyncio
import asyncpg
from pathlib import Path

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "bd_santiago_munoz_nakamoto")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

async def run_seed():
    print(f"Connecting to {DB_NAME} at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    try:
        # First connect to postgres database to ensure target database exists
        sys_conn = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database="postgres"
        )
        db_exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME
        )
        if not db_exists:
            print(f"Database {DB_NAME} does not exist. Creating...")
            await sys_conn.execute(f'CREATE DATABASE "{DB_NAME}";')
        await sys_conn.close()

        # Connect to target database
        conn = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        
        sql_files = [
            "01_schema.sql",
            "02_security_rls.sql",
            "03_functions_procedures.sql",
            "04_queries.sql",
            "05_seed.sql"
        ]

        for fname in sql_files:
            fpath = SQL_DIR / fname
            if fpath.exists():
                print(f"Executing {fname}...")
                sql_content = fpath.read_text(encoding="utf-8")
                await conn.execute(sql_content)
                print(f"  ✓ {fname} executed successfully.")
            else:
                print(f"  ✗ {fname} not found!")

        user_count = await conn.fetchval("SELECT COUNT(*) FROM rw_users;")
        msg_count = await conn.fetchval("SELECT COUNT(*) FROM rw_messages;")
        print(f"\n✓ Seed complete! {user_count} users, {msg_count} messages in database.")
        await conn.close()

    except Exception as e:
        print(f"Error executing seed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_seed())

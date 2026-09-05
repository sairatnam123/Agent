import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def connection() -> psycopg.Connection:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg.connect(database_url, row_factory=dict_row)

    settings = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    missing = [
        name for name, value in {
            "DB_HOST": settings["host"],
            "DB_NAME": settings["dbname"],
            "DB_USER": settings["user"],
            "DB_PASSWORD": settings["password"],
        }.items()
        if not value
    ]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Missing database environment variables: {names}")

    return psycopg.connect(**settings, row_factory=dict_row)
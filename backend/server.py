from typing import Any

import psycopg
from mcp.server import MCPServer

from database import connection

mcp = MCPServer("users-products")


def database():
    return connection()


def initialize_database() -> None:
    with database() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);")
        connection.execute("CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', price REAL NOT NULL CHECK (price >= 0), stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);")


def rows_as_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


@mcp.tool()
async def count_users() -> dict[str, int]:
    """Return the total number of users."""
    with database() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    return {"count": int(row["count"])}



@mcp.tool()
async def list_users(limit: int = 50) -> list[dict[str, Any]]:
    """List users, newest first."""
    with database() as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY id DESC LIMIT %s", (max(1, min(limit, 100)),)).fetchall()
    return rows_as_json(rows)


@mcp.tool()
async def get_user(user_id: int) -> dict[str, Any]:
    """Get a user by ID."""
    with database() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
    return dict(row) if row else {"error": "User not found."}


@mcp.tool()
async def list_products(limit: int = 50) -> list[dict[str, Any]]:
    """List products, newest first."""
    with database() as connection:
        rows = connection.execute("SELECT * FROM products ORDER BY id DESC LIMIT %s", (max(1, min(limit, 100)),)).fetchall()
    return rows_as_json(rows)


@mcp.tool()
async def count_products() -> dict[str, int]:
    """Return the total number of products."""
    with database() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM products").fetchone()
    return {"count": int(row["count"])}


@mcp.tool()
async def get_product(product_id: int) -> dict[str, Any]:
    """Get a product by ID."""
    with database() as connection:
        row = connection.execute("SELECT * FROM products WHERE id = %s", (product_id,)).fetchone()
    return dict(row) if row else {"error": "Product not found."}


@mcp.tool()
async def search_products(query: str) -> list[dict[str, Any]]:
    """Search products by name or description."""
    pattern = f"%{query.strip()}%"
    with database() as connection:
        rows = connection.execute("SELECT * FROM products WHERE name ILIKE %s OR description ILIKE %s ORDER BY id DESC", (pattern, pattern)).fetchall()
    return rows_as_json(rows)


if __name__ == "__main__":
    initialize_database()
    mcp.run(transport="stdio")

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field

from database import connection

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
PYTHON_MCP_SERVER_PATH = Path(__file__).resolve().parent / "server.py"
app = FastAPI()
chat_agent = None
database_agent = None
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Agent API is running"}


def initialize_database() -> None:
    with connection() as database:
        database.execute("CREATE TABLE IF NOT EXISTS conversations (id SERIAL PRIMARY KEY, title TEXT NOT NULL DEFAULT 'New Chat', created_at TEXT NOT NULL);")
        database.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, conversation_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY (conversation_id) REFERENCES conversations(id));")


def create_conversation(title: str) -> int:
    with connection() as database:
        cursor = database.execute("INSERT INTO conversations (title, created_at) VALUES (%s, %s) RETURNING id", (title, datetime.now(timezone.utc).isoformat()))
        return int(cursor.fetchone()["id"])


def save_message(conversation_id: int, role: str, content: str) -> None:
    with connection() as database:
        database.execute("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (%s, %s, %s, %s)", (conversation_id, role, content, datetime.now(timezone.utc).isoformat()))


def conversation_messages(conversation_id: int) -> list[dict[str, str]]:
    with connection() as database:
        rows = database.execute("SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY id", (conversation_id,)).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in rows]


def mcp_parameters() -> StdioServerParameters:
    return StdioServerParameters(command=sys.executable, args=[str(PYTHON_MCP_SERVER_PATH)], cwd=str(PYTHON_MCP_SERVER_PATH.parent), env=os.environ.copy())


async def call_mcp_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with stdio_client(mcp_parameters()) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            if result.is_error:
                raise RuntimeError(f"MCP tool '{name}' failed")
            text = next((item.text for item in result.content if hasattr(item, "text")), "null")
            return json.loads(text)



@tool
async def list_users_for_agent() -> list[dict[str, Any]]:
    """List users through the MCP PostgreSQL server."""
    return await call_mcp_tool("list_users", {})


@tool
async def count_users_for_agent() -> dict[str, int]:
    """Count users through the MCP PostgreSQL server."""
    return await call_mcp_tool("count_users", {})


@tool
async def get_user_for_agent(user_id: int) -> dict[str, Any]:
    """Get one user by ID through the MCP PostgreSQL server."""
    return await call_mcp_tool("get_user", {"user_id": user_id})


@tool
async def list_products_for_agent() -> list[dict[str, Any]]:
    """List products through the MCP PostgreSQL server."""
    return await call_mcp_tool("list_products", {})


@tool
async def count_products_for_agent() -> dict[str, int]:
    """Count products through the MCP PostgreSQL server."""
    return await call_mcp_tool("count_products", {})


@tool
async def get_product_for_agent(product_id: int) -> dict[str, Any]:
    """Get one product by ID through the MCP PostgreSQL server."""
    return await call_mcp_tool("get_product", {"product_id": product_id})


@tool
async def search_products_for_agent(query: str) -> list[dict[str, Any]]:
    """Search products through the MCP PostgreSQL server."""
    return await call_mcp_tool("search_products", {"query": query})


def create_ollama_agent(tools: list[Any], system_prompt: str) -> Any:
    base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434").removesuffix("/v1")
    return create_agent(
        model=ChatOllama(model=os.getenv("OPENAI_MODEL", "llama3.2"), base_url=base_url),
        tools=tools,
        system_prompt=system_prompt,
    )



def get_database_agent() -> Any:
    global database_agent
    if database_agent is None:
        database_agent = create_ollama_agent(
            [
                list_users_for_agent,
                count_users_for_agent,
                get_user_for_agent,
                list_products_for_agent,
                count_products_for_agent,
                get_product_for_agent,
                search_products_for_agent,
            ],
            "You are a PostgreSQL store assistant. Use database tools only for explicit "
            "user or product requests. Never invent records or claim a database action "
            "without a confirmed tool result. When a user asks to list, show, search, or "
            "display users or products, call the appropriate tool and present its result as "
            "a Markdown table. For users use the columns ID, Name, Email, and Created At. "
            "For products use the columns ID, Name, Price, Stock, Description, and Created At. "
            "If no records are returned, say that no matching records were found.",
        )
    return database_agent


def get_chat_agent() -> Any:
    global chat_agent
    if chat_agent is None:
        chat_agent = create_ollama_agent(
            [],
            "You are a helpful normal conversational assistant. Answer general questions, "
            "greetings, explanations, writing, and coding questions directly. Do not use "
            "or mention database tools unless the user explicitly asks about users or products.",
        )
    return chat_agent


def is_database_request(message: str) -> bool:
    text = message.lower()
    has_entity = re.search(r"\b(user|users|product|products)\b", text)
    has_action = re.search(
        r"\b(list|show|find|search|get|retrieve|look up|available|stock|price|count|counts|number|many)\b",
        text,
    )
    return bool(has_entity and has_action)


def parse_record_lookup(message: str) -> tuple[str, int] | None:
    match = re.search(
        r"\b(get|find|retrieve|show|look\s+up)\s+(?:the\s+)?(user|product)\s+(?:id\s*(?:is\s*)?)?(\d+)\b",
        message.lower(),
    )
    if not match:
        return None
    return match.group(2), int(match.group(3))


def message_text(message: Any) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") for part in content if isinstance(part, dict))


def is_tool_payload(text: str) -> bool:
    try:
        payload = json.loads(text.strip().strip("`"))
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and "name" in payload and (
        "parameters" in payload or "args" in payload
    )


async def execute_tool_payload(text: str) -> tuple[str, dict[str, Any]] | None:
    try:
        payload = json.loads(text.strip().strip("`"))
    except json.JSONDecodeError:
        return None
    name = payload.get("name") if isinstance(payload, dict) else None
    arguments = payload.get("parameters") or payload.get("args") or {}
    tool_map = {
        "list_users_for_agent": "list_users",
        "count_users_for_agent": "count_users",
        "get_user_for_agent": "get_user",
        "list_products_for_agent": "list_products",
        "count_products_for_agent": "count_products",
        "get_product_for_agent": "get_product",
        "search_products_for_agent": "search_products",
    }
    mcp_name = tool_map.get(name)
    if not mcp_name:
        return None
    result = await call_mcp_tool(mcp_name, arguments)
    return json.dumps(result, default=str), {"name": name, "args": arguments}


@app.on_event("startup")
async def startup() -> None:
    initialize_database()


@app.get("/conversations")
async def conversations() -> list[dict[str, Any]]:
    with connection() as database:
        rows = database.execute("SELECT id, title, created_at FROM conversations ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.get("/conversations/{conversation_id}/messages")
async def messages(conversation_id: int) -> list[dict[str, str]]:
    return conversation_messages(conversation_id)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or create_conversation(request.message[:40])
    save_message(conversation_id, "user", request.message)
    try:
        lookup = parse_record_lookup(request.message)
        if lookup:
            record_type, record_id = lookup
            tool_name = "get_user" if record_type == "user" else "get_product"
            result = await call_mcp_tool(tool_name, {f"{record_type}_id": record_id})
            response = json.dumps(result, default=str)
            tool_calls = [{"name": tool_name, "args": {f"{record_type}_id": record_id}}]
            save_message(conversation_id, "assistant", response)
            return ChatResponse(response=response, conversation_id=conversation_id, tool_calls=tool_calls)
        history = conversation_messages(conversation_id)
        agent = get_database_agent() if is_database_request(request.message) else get_chat_agent()
        result = await agent.ainvoke({"messages": history})
        response = ""
        executed_tool_call = None
        for message in reversed(result["messages"]):
            text = message_text(message).strip()
            if is_tool_payload(text):
                executed = await execute_tool_payload(text)
                if executed:
                    response, executed_tool_call = executed
                    break
            if getattr(message, "type", "") == "ai" and text and not getattr(message, "tool_calls", None):
                response = text
                break
        if not response:
            response = "I could not produce a final answer."
        tool_calls = [{"name": call["name"], "args": call["args"]} for message in result["messages"] for call in getattr(message, "tool_calls", [])]
        if executed_tool_call:
            tool_calls.append(executed_tool_call)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Model request failed: {error}") from error
    save_message(conversation_id, "assistant", response)
    return ChatResponse(response=response, conversation_id=conversation_id, tool_calls=tool_calls)

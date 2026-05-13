from mcp.server.fastmcp import FastMCP

from chat_store import (
    create_chat_session,
    add_chat_message,
    get_chat_history,
    list_chat_sessions,
    clear_chat_session,
)


mcp = FastMCP("Chat Memory Tools")


@mcp.tool()
def create_session(title: str = "New Chat") -> dict:
    """
    Create a new local chat session.
    """
    return create_chat_session(title=title)


@mcp.tool()
def save_message(session_id: str, role: str, content: str) -> dict:
    """
    Save one chat message to local SQLite history.

    role must be one of:
    user, assistant, system
    """
    return add_chat_message(
        session_id=session_id,
        role=role,
        content=content,
    )


@mcp.tool()
def read_history(session_id: str, limit: int = 20) -> list:
    """
    Read recent messages from one chat session.
    """
    return get_chat_history(
        session_id=session_id,
        limit=limit,
    )


@mcp.tool()
def list_sessions(limit: int = 20) -> list:
    """
    List recent chat sessions.
    """
    return list_chat_sessions(limit=limit)


@mcp.tool()
def clear_session(session_id: str) -> dict:
    """
    Clear all messages from one chat session.
    """
    return clear_chat_session(session_id=session_id)


if __name__ == "__main__":
    mcp.run()
from mcp.server.fastmcp import FastMCP

from app.models.document import get_all_documents, get_document_by_id
from app.models.document_chunks import search_chunks
from app.models.chat_sessions import get_all_sessions
from app.db.postgres import get_cursor

mcp = FastMCP("data")


def _stringify_dates(rows):
    for row in rows:
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                row[key] = value.isoformat()
    return rows


@mcp.tool()
def list_documents() -> list[dict]:
    """List every uploaded document with its id, file name, status, and chunk count."""
    return _stringify_dates(get_all_documents())


@mcp.tool()
def get_document(document_id: int) -> dict:
    """Get full details for a single document by its id. Returns an empty dict if not found."""
    doc = get_document_by_id(document_id)
    if doc is None:
        return {}
    return _stringify_dates([doc])[0]


@mcp.tool()
def search_documents(query: str) -> list[dict]:
    """Full-text search across all document chunks for a keyword or phrase."""
    return search_chunks(query)


@mcp.tool()
def document_stats() -> dict:
    """Aggregate stats: total documents, total chunks, and a breakdown of document status counts."""
    with get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM documents")
        total_documents = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM document_chunks")
        total_chunks = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM documents
            GROUP BY status
            """
        )
        status_breakdown = cursor.fetchall()

    return {
        "total_documents": total_documents,
        "total_chunks": total_chunks,
        "status_breakdown": status_breakdown,
    }


@mcp.tool()
def chat_session_stats() -> dict:
    """List chat sessions with their titles and creation times, plus a total count."""
    sessions = _stringify_dates(get_all_sessions())
    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
    }


if __name__ == "__main__":
    mcp.run()

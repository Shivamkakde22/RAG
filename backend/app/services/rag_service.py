from app.services.orchestrator import orchestrate


def ask_rag(query: str, document_id: int = None) -> dict:
    return orchestrate(query, document_id=document_id)

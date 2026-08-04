from app.services.retriever import retrieve
from app.services.reranker import rerank
from app.services.llm_service import (
    classify_query,
    decompose_query,
    generate_answer,
    generate_summary,
    synthesize_multi_part,
)
from app.services.agent_service import run_agentic_chat

OUT_OF_SCOPE_REPLY = (
    "• **Out of Scope**\n\n"
    "- This question does not appear to relate to your uploaded documents.\n"
    "- Please ask something about the content in your documents."
)


def orchestrate(query: str, document_id: int = None) -> dict:
    query_type = classify_query(query)
    print(f"[Orchestrator] query_type={query_type!r} | query={query[:60]!r}")

    if query_type == "out_of_scope":
        return _handle_agentic(query)

    if query_type == "summarization":
        return _handle_summarization(query, document_id)

    if query_type == "multi_part":
        return _handle_multi_part(query, document_id)

    return _handle_simple(query, document_id)


def _handle_agentic(query: str) -> dict:
    try:
        result = run_agentic_chat(query)
    except Exception as e:
        print(f"[Orchestrator] agent error: {e}")
        result = None

    if result is None:
        return {
            "query": query,
            "query_type": "out_of_scope",
            "chunks": [],
            "answer": OUT_OF_SCOPE_REPLY,
        }

    return {
        "query": query,
        "query_type": "tool_use",
        "chunks": [],
        "answer": result["answer"],
        "tools_used": result["tools_used"],
    }


def _handle_simple(query: str, document_id: int | None) -> dict:
    candidates = retrieve(query, document_id=document_id, candidate_k=20)
    chunks = rerank(query, candidates, top_k=5)
    answer = generate_answer(query, chunks)
    return {
        "query": query,
        "query_type": "simple",
        "chunks": chunks,
        "answer": answer,
    }


def _handle_summarization(query: str, document_id: int | None) -> dict:
    candidates = retrieve(query, document_id=document_id, candidate_k=30)
    chunks = rerank(query, candidates, top_k=10)
    answer = generate_summary(query, chunks)
    return {
        "query": query,
        "query_type": "summarization",
        "chunks": chunks,
        "answer": answer,
    }


def _handle_multi_part(query: str, document_id: int | None) -> dict:
    sub_queries = decompose_query(query)
    print(f"[Orchestrator] sub_queries={sub_queries}")

    merged: dict[str, float] = {}
    for sub_q in sub_queries:
        for text, score in retrieve(sub_q, document_id=document_id, candidate_k=20):
            if text not in merged or score > merged[text]:
                merged[text] = score

    candidates = sorted(merged.items(), key=lambda x: x[1], reverse=True)[:30]
    chunks = rerank(query, candidates, top_k=7)
    answer = synthesize_multi_part(query, chunks, sub_queries)

    return {
        "query": query,
        "query_type": "multi_part",
        "sub_queries": sub_queries,
        "chunks": chunks,
        "answer": answer,
    }

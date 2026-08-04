import concurrent.futures

from app.services.embedding_service import embed
from app.db.qdrant import similarity_search
from app.services.bm25_service import bm25_search
from app.services.fusion import reciprocal_rank_fusion

SCORE_THRESHOLD = 0.25
CANDIDATE_K = 20


def retrieve(
    query: str,
    document_id: int = None,
    candidate_k: int = CANDIDATE_K
) -> list[tuple[str, float]]:
    query_vector = embed(query)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_vector = executor.submit(
            similarity_search, query_vector, document_id, candidate_k
        )
        future_bm25 = executor.submit(
            bm25_search, query, document_id, candidate_k
        )
        vector_hits = future_vector.result()
        bm25_ranked = future_bm25.result()

    vector_ranked = [
        (hit.payload["chunk_text"], round(hit.score, 4))
        for hit in vector_hits
        if hit.score >= SCORE_THRESHOLD
    ]

    fused = reciprocal_rank_fusion(vector_ranked, bm25_ranked)
    return fused[:candidate_k]

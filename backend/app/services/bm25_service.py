import re
from rank_bm25 import BM25Okapi
from app.models.document_chunks import get_chunks_by_document, get_all_chunks


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def bm25_search(
    query: str,
    document_id: int = None,
    top_k: int = 20
) -> list[tuple[str, float]]:
    if document_id is not None:
        rows = get_chunks_by_document(document_id)
    else:
        rows = get_all_chunks()

    if not rows:
        return []

    corpus = [row["chunk_text"] for row in rows]
    tokenized_corpus = [_tokenize(text) for text in corpus]

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(_tokenize(query))

    ranked = sorted(
        zip(corpus, scores.tolist()),
        key=lambda x: x[1],
        reverse=True
    )

    return [(text, score) for text, score in ranked[:top_k] if score > 0]

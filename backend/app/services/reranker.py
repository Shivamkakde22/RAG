from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(_MODEL_NAME)
    return _model


def rerank(
    query: str,
    candidates: list[tuple[str, float]],
    top_k: int = 5
) -> list[str]:
    if not candidates:
        return []

    model = _get_model()
    texts = [text for text, _ in candidates]
    pairs = [[query, text] for text in texts]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(texts, scores),
        key=lambda x: x[1],
        reverse=True
    )
    return [text for text, _ in ranked[:top_k]]

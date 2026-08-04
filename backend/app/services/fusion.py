def reciprocal_rank_fusion(
    *rankings: list[tuple[str, float]],
    k: int = 60
) -> list[tuple[str, float]]:
    """
    Merge multiple ranked lists with Reciprocal Rank Fusion.
    RRF score = sum of 1 / (k + rank) across all lists.
    k=60 is the standard constant that dampens high-rank dominance.
    """
    scores: dict[str, float] = {}

    for ranking in rankings:
        for rank, (text, _) in enumerate(ranking):
            scores[text] = scores.get(text, 0.0) + 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

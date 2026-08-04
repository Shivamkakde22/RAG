import json
import numpy as np
from app.services.llm_service import _call_llm
from app.services.embedding_service import embed


def evaluate(query: str, answer: str, chunks: list[str]) -> dict:
    faithfulness_score, faithfulness_detail = _faithfulness(answer, chunks)
    context_precision_score, context_precision_detail = _context_precision(query, chunks)
    answer_relevancy_score = _answer_relevancy(query, answer)

    overall = round(
        (faithfulness_score + context_precision_score + answer_relevancy_score) / 3,
        3
    )

    return {
        "scores": {
            "faithfulness": faithfulness_score,
            "context_precision": context_precision_score,
            "answer_relevancy": answer_relevancy_score,
            "overall": overall,
        },
        "details": {
            "faithfulness": faithfulness_detail,
            "context_precision": context_precision_detail,
        },
    }


def _faithfulness(answer: str, chunks: list[str]) -> tuple[float, str]:
    if not chunks or not answer:
        return 0.0, "Nothing to evaluate"

    context = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(chunks))

    prompt = f"""You are an evaluation assistant. Read the context passages and the answer below.
Identify every distinct factual claim made in the answer.
Count how many of those claims are directly supported by the context.

CONTEXT:
{context}

ANSWER:
{answer}

Respond with ONLY valid JSON in this exact format (no explanation):
{{"supported_claims": <integer>, "total_claims": <integer>}}"""

    result = _call_llm(prompt, retries=2)
    if result:
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            data = json.loads(result[start:end])
            supported = max(0, int(data.get("supported_claims", 0)))
            total = max(1, int(data.get("total_claims", 1)))
            score = round(min(supported / total, 1.0), 3)
            return score, f"{supported}/{total} claims supported by context"
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    return 0.0, "Could not evaluate"


def _context_precision(query: str, chunks: list[str]) -> tuple[float, str]:
    if not chunks:
        return 0.0, "No chunks to evaluate"

    chunk_list = "\n".join(
        f"[{i+1}] {c[:300]}..." for i, c in enumerate(chunks)
    )

    prompt = f"""You are an evaluation assistant.
Given the question and context passages, identify which passage numbers are actually useful for answering the question.

QUESTION: {query}

CONTEXT PASSAGES:
{chunk_list}

Respond with ONLY a valid JSON array of relevant passage numbers (1-indexed). Example: [1, 3]
If none are relevant, return: []"""

    result = _call_llm(prompt, retries=2)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            relevant = json.loads(result[start:end])
            relevant = [r for r in relevant if isinstance(r, int) and 1 <= r <= len(chunks)]
            score = round(len(relevant) / len(chunks), 3)
            return score, f"{len(relevant)}/{len(chunks)} chunks relevant to query"
        except (json.JSONDecodeError, ValueError):
            pass
    return 0.0, "Could not evaluate"


def _answer_relevancy(query: str, answer: str) -> float:
    if not answer or not query:
        return 0.0

    skip_phrases = ("error", "no relevant content", "could not find", "out of scope")
    if any(p in answer.lower() for p in skip_phrases):
        return 0.0

    q_vec = np.array(embed(query))
    a_vec = np.array(embed(answer[:600]))

    norm = np.linalg.norm(q_vec) * np.linalg.norm(a_vec)
    if norm == 0:
        return 0.0

    similarity = float(np.dot(q_vec, a_vec) / norm)
    return round(max(0.0, min(similarity, 1.0)), 3)

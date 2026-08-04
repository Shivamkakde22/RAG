"""
RAG Pipeline Test Runner
========================
Phases:
  1. generate  -- create questions from chunks (uses Gemini)
  2. retrieval -- test hybrid retrieval on all questions (no LLM)
  3. pipeline  -- full pipeline + RAGAS on a sample (uses Gemini)

Usage:
  python run_pipeline_test.py --all               # run all 3 phases
  python run_pipeline_test.py --generate          # phase 1: questions via Gemini
  python run_pipeline_test.py --generate-offline  # phase 1: questions via templates (no LLM)
  python run_pipeline_test.py --retrieval         # phase 2 only
  python run_pipeline_test.py --pipeline 50       # phase 3 with 50 questions
  python run_pipeline_test.py --report            # print report from saved results
"""

import argparse
import json
import csv
import time
import os
import random
import traceback
from datetime import datetime

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
DATA_DIR    = os.path.join(BASE_DIR, "test_data")
Q_FILE      = os.path.join(DATA_DIR, "questions.json")
RET_FILE    = os.path.join(DATA_DIR, "retrieval_results.json")
PIPE_FILE   = os.path.join(DATA_DIR, "pipeline_results.json")
REPORT_CSV  = os.path.join(DATA_DIR, "test_report.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# ── rate limiter ───────────────────────────────────────────────────────────────
_last_call_ts = 0.0
MIN_INTERVAL  = 4.5   # seconds between Gemini calls → ~13 RPM (under 15 RPM limit)

def _gemini_sleep():
    global _last_call_ts
    elapsed = time.time() - _last_call_ts
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_call_ts = time.time()


# ── helpers ────────────────────────────────────────────────────────────────────
def _load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _progress(current, total, label=""):
    pct = int(current / total * 40)
    bar = "#" * pct + "-" * (40 - pct)
    print(f"\r[{bar}] {current}/{total} {label}", end="", flush=True)


# ── Phase 1a: Offline Question Generation (no LLM) ────────────────────────────
_PYTHON_TEMPLATES = [
    "What is {concept} in Python?",
    "How does {concept} work in Python?",
    "Explain {concept} as described in the document.",
    "What are the features or uses of {concept} in Python?",
    "How is {concept} defined or used according to the text?",
]

_STOP_WORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "must","shall","can","need","dare","ought","used","to","of","in","for",
    "on","with","at","by","from","as","into","through","during","before",
    "after","above","below","up","down","out","off","over","under","again",
    "further","then","once","and","or","but","if","while","although","because",
    "since","unless","until","this","that","these","those","it","its","we",
    "they","them","their","there","here","when","where","which","who","whom",
    "what","how","why","not","no","nor","so","yet","both","either","neither",
    "each","few","more","most","other","some","such","than","too","very",
    "just","only","also","all","any","both","each","every","i","you","he",
    "she","him","her","his","our","your","my","me","us","python","following",
}

def _extract_concept(text: str) -> str:
    """Extract a short concept phrase from chunk text."""
    import re
    # Try to get the first sentence
    first_sent = re.split(r'[.!?\n]', text.strip())[0][:120].strip()
    # Remove intro patterns
    first_sent = re.sub(
        r'^(introduction to|what is|definition of|overview of|'
        r'concept of|types of|examples? of)\s*', '',
        first_sent, flags=re.IGNORECASE
    ).strip()

    # If short enough, return as-is
    if 5 < len(first_sent) < 60:
        return first_sent

    # Otherwise pick top keywords
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    from collections import Counter
    counts = Counter(w for w in words if w not in _STOP_WORDS)
    top = [w for w, _ in counts.most_common(3)]
    return " ".join(top) if top else "this concept"


def generate_questions_offline():
    """Generate questions from chunk text without using any LLM."""
    import re
    from app.models.document_chunks import get_all_chunks

    existing = _load_json(Q_FILE, [])
    done_keys = {(q["document_id"], q["chunk_index"]) for q in existing}

    chunks = get_all_chunks()
    pending = [
        c for c in chunks
        if (c["document_id"], c["chunk_index"]) not in done_keys
    ]

    print(f"\n── Phase 1 (offline): Question Generation ────────────────────")
    print(f"  Total chunks : {len(chunks)}")
    print(f"  Already done : {len(done_keys)}")
    print(f"  Generating   : {len(pending)}")

    questions = list(existing)

    for i, chunk in enumerate(pending):
        text    = chunk["chunk_text"]
        concept = _extract_concept(text)
        template = _PYTHON_TEMPLATES[i % len(_PYTHON_TEMPLATES)]
        question = template.format(concept=concept)

        questions.append({
            "question"    : question,
            "document_id" : chunk["document_id"],
            "chunk_index" : chunk["chunk_index"],
            "source_text" : text[:300],
            "generated_by": "template",
        })

        if (i + 1) % 25 == 0:
            _save_json(Q_FILE, questions)
            _progress(i + 1, len(pending), "offline questions")

    _save_json(Q_FILE, questions)
    print(f"\n  Done. Total questions: {len(questions)}")
    return questions


# ── Phase 1b: LLM Question Generation ─────────────────────────────────────────
def generate_questions(batch_size=5):
    from app.models.document_chunks import get_all_chunks
    from app.services.llm_service import _call_llm

    existing = _load_json(Q_FILE, [])
    done_indices = {q["chunk_index"] for q in existing}

    chunks = get_all_chunks()
    pending = [c for c in chunks if c["chunk_index"] not in done_indices]

    print(f"\n── Phase 1: Question Generation ──────────────────────────────")
    print(f"  Total chunks : {len(chunks)}")
    print(f"  Already done : {len(done_indices)}")
    print(f"  Remaining    : {len(pending)}")

    questions = list(existing)

    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        snippets = "\n\n".join(
            f"[Passage {j+1}]\n{c['chunk_text'][:600]}"
            for j, c in enumerate(batch)
        )

        prompt = f"""Given the following passages from a Python programming textbook,
generate exactly ONE clear, specific question for EACH passage.
The question should be answerable from that passage alone.

{snippets}

Respond ONLY with a JSON array of {len(batch)} question strings in the same order as the passages.
Example: ["What is X?", "How does Y work?", ...]"""

        _gemini_sleep()
        raw = _call_llm(prompt, retries=3)

        generated = []
        if raw:
            try:
                start = raw.find("[")
                end   = raw.rfind("]") + 1
                generated = json.loads(raw[start:end])
                if not isinstance(generated, list):
                    generated = []
            except Exception:
                generated = []

        # Pad with fallbacks if Gemini returned fewer than expected
        while len(generated) < len(batch):
            generated.append(None)

        for chunk, q_text in zip(batch, generated):
            if q_text and isinstance(q_text, str) and len(q_text) > 10:
                questions.append({
                    "question"    : q_text.strip(),
                    "document_id" : chunk["document_id"],
                    "chunk_index" : chunk["chunk_index"],
                    "source_text" : chunk["chunk_text"][:300],
                })

        _save_json(Q_FILE, questions)
        _progress(min(i + batch_size, len(pending)), len(pending), "questions generated")

    print(f"\n  Done. Total questions saved: {len(questions)}")
    return questions


# ── Phase 2: Retrieval Tests ───────────────────────────────────────────────────
def run_retrieval_tests(questions):
    from app.services.retriever import retrieve

    existing = {r["question"]: r for r in _load_json(RET_FILE, [])}

    print(f"\n── Phase 2: Retrieval Tests ──────────────────────────────────")
    print(f"  Questions   : {len(questions)}")
    print(f"  Already done: {len(existing)}")

    results = list(existing.values())

    pending = [q for q in questions if q["question"] not in existing]
    print(f"  Running     : {len(pending)}")

    for idx, q in enumerate(pending):
        t0 = time.time()
        try:
            candidates = retrieve(q["question"], document_id=None, candidate_k=20)
            latency    = round(time.time() - t0, 3)
            scores     = [s for _, s in candidates]
            results.append({
                "question"      : q["question"],
                "document_id"   : q["document_id"],
                "n_retrieved"   : len(candidates),
                "top_score"     : round(max(scores), 4) if scores else 0,
                "avg_score"     : round(sum(scores) / len(scores), 4) if scores else 0,
                "latency_s"     : latency,
                "status"        : "ok" if candidates else "empty",
            })
        except Exception as e:
            results.append({
                "question"    : q["question"],
                "document_id" : q["document_id"],
                "status"      : "error",
                "error"       : str(e),
            })

        if (idx + 1) % 10 == 0:
            _save_json(RET_FILE, results)
            _progress(idx + 1, len(pending), "retrieval tests")

    _save_json(RET_FILE, results)
    print(f"\n  Done. {len(results)} retrieval results saved.")
    return results


# ── Phase 3: Full Pipeline + RAGAS ────────────────────────────────────────────
def run_pipeline_tests(questions, n_sample=50):
    from app.services.rag_service import ask_rag
    from app.services.ragas_evaluator import evaluate

    existing = {r["question"]: r for r in _load_json(PIPE_FILE, [])}

    pool    = [q for q in questions if q["question"] not in existing]
    random.shuffle(pool)
    pending = pool[:max(0, n_sample - len(existing))]

    print(f"\n── Phase 3: Full Pipeline + RAGAS ───────────────────────────")
    print(f"  Target sample  : {n_sample}")
    print(f"  Already done   : {len(existing)}")
    print(f"  Running now    : {len(pending)}")
    print(f"  Est. Gemini calls: ~{len(pending) * 4} (classify+gen+faithful+precision)")
    est_min = round(len(pending) * 4 * MIN_INTERVAL / 60, 1)
    print(f"  Est. time      : ~{est_min} min (at {MIN_INTERVAL}s/call)")

    results = list(existing.values())

    for idx, q in enumerate(pending):
        t0 = time.time()
        try:
            rag_result = ask_rag(q["question"], document_id=None)
            rag_latency = round(time.time() - t0, 3)

            answer = rag_result.get("answer", "")
            chunks = rag_result.get("chunks", [])
            qtype  = rag_result.get("query_type", "unknown")

            eval_result = evaluate(q["question"], answer, chunks)
            total_latency = round(time.time() - t0, 3)

            results.append({
                "question"         : q["question"],
                "document_id"      : q["document_id"],
                "query_type"       : qtype,
                "answer_preview"   : answer[:200],
                "n_chunks"         : len(chunks),
                "faithfulness"     : eval_result["scores"]["faithfulness"],
                "context_precision": eval_result["scores"]["context_precision"],
                "answer_relevancy" : eval_result["scores"]["answer_relevancy"],
                "overall"          : eval_result["scores"]["overall"],
                "faithfulness_detail"     : eval_result["details"]["faithfulness"],
                "context_precision_detail": eval_result["details"]["context_precision"],
                "rag_latency_s"    : rag_latency,
                "total_latency_s"  : total_latency,
                "status"           : "ok",
            })

        except Exception as e:
            results.append({
                "question"   : q["question"],
                "document_id": q["document_id"],
                "status"     : "error",
                "error"      : str(e),
            })
            traceback.print_exc()

        _save_json(PIPE_FILE, results)
        ok = [r for r in results if r.get("status") == "ok"]
        avg = round(sum(r["overall"] for r in ok) / len(ok), 3) if ok else 0
        _progress(idx + 1, len(pending), f"| avg RAGAS={avg}")

    print(f"\n  Done. {len(results)} pipeline results saved.")
    return results


# ── Report ─────────────────────────────────────────────────────────────────────
def print_report():
    questions  = _load_json(Q_FILE,    [])
    ret_res    = _load_json(RET_FILE,  [])
    pipe_res   = _load_json(PIPE_FILE, [])

    print("\n" + "=" * 60)
    print("  RAG PIPELINE TEST REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    print(f"\n📋 Questions Generated : {len(questions)}")

    # ── Retrieval stats
    if ret_res:
        ok  = [r for r in ret_res if r.get("status") == "ok"]
        empty = [r for r in ret_res if r.get("status") == "empty"]
        err = [r for r in ret_res if r.get("status") == "error"]

        avg_top   = round(sum(r.get("top_score", 0)  for r in ok) / len(ok), 4) if ok else 0
        avg_lat   = round(sum(r.get("latency_s", 0)  for r in ok) / len(ok), 3) if ok else 0
        avg_n     = round(sum(r.get("n_retrieved", 0) for r in ok) / len(ok), 1) if ok else 0

        print(f"\n🔍 Retrieval Tests ({len(ret_res)} questions)")
        print(f"   ✅ Successful       : {len(ok)}")
        print(f"   ⚠️  Empty results   : {len(empty)}")
        print(f"   ❌ Errors          : {len(err)}")
        print(f"   Avg chunks/query   : {avg_n}")
        print(f"   Avg top score      : {avg_top}")
        print(f"   Avg latency        : {avg_lat}s")

    # ── Pipeline stats
    if pipe_res:
        ok  = [r for r in pipe_res if r.get("status") == "ok"]
        err = [r for r in pipe_res if r.get("status") == "error"]

        def avg(key):
            vals = [r[key] for r in ok if key in r]
            return round(sum(vals) / len(vals), 3) if vals else 0

        print(f"\n🤖 Full Pipeline Tests ({len(pipe_res)} questions)")
        print(f"   ✅ Successful       : {len(ok)}")
        print(f"   ❌ Errors          : {len(err)}")
        print(f"   Faithfulness       : {avg('faithfulness')}")
        print(f"   Context Precision  : {avg('context_precision')}")
        print(f"   Answer Relevancy   : {avg('answer_relevancy')}")
        print(f"   ── Overall RAGAS   : {avg('overall')}")
        print(f"   Avg RAG latency    : {avg('rag_latency_s')}s")
        print(f"   Avg total latency  : {avg('total_latency_s')}s")

        # Query type breakdown
        from collections import Counter
        types = Counter(r.get("query_type", "?") for r in ok)
        print(f"\n   Query type breakdown:")
        for t, n in types.most_common():
            print(f"     {t:20s}: {n}")

        # Score distribution
        scores = [r["overall"] for r in ok if "overall" in r]
        if scores:
            hi = sum(1 for s in scores if s >= 0.7)
            mid = sum(1 for s in scores if 0.4 <= s < 0.7)
            lo = sum(1 for s in scores if s < 0.4)
            print(f"\n   Score distribution (overall):")
            print(f"     🟢 ≥70%  : {hi}  ({round(hi/len(scores)*100)}%)")
            print(f"     🟡 40–69%: {mid} ({round(mid/len(scores)*100)}%)")
            print(f"     🔴 <40%  : {lo}  ({round(lo/len(scores)*100)}%)")

        # Save CSV
        _write_csv(ok)

    print("\n" + "=" * 60)
    print(f"  Results saved in: {DATA_DIR}")
    print("=" * 60 + "\n")


def _write_csv(results):
    if not results:
        return
    fields = [
        "question", "query_type", "faithfulness", "context_precision",
        "answer_relevancy", "overall", "n_chunks",
        "rag_latency_s", "faithfulness_detail", "context_precision_detail"
    ]
    with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print(f"\n   CSV report saved: {REPORT_CSV}")


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline Test Runner")
    parser.add_argument("--all",              action="store_true", help="Run all 3 phases")
    parser.add_argument("--generate",         action="store_true", help="Phase 1: generate questions via Gemini")
    parser.add_argument("--generate-offline", action="store_true", dest="generate_offline",
                        help="Phase 1: generate questions via templates (no LLM)")
    parser.add_argument("--retrieval",        action="store_true", help="Phase 2: retrieval tests")
    parser.add_argument("--pipeline",  type=int, nargs="?", const=50,
                        metavar="N",  help="Phase 3: full pipeline tests on N questions (default 50)")
    parser.add_argument("--report",    action="store_true", help="Print report from saved results")
    args = parser.parse_args()

    if not any([args.all, args.generate, args.retrieval, args.pipeline, args.report]):
        parser.print_help()
        return

    questions = []

    if args.generate_offline:
        questions = generate_questions_offline()
    elif args.all or args.generate:
        questions = generate_questions(batch_size=5)
    else:
        questions = _load_json(Q_FILE, [])

    if not questions and (args.retrieval or args.pipeline):
        print("No questions found. Run --generate first.")
        return

    if args.all or args.retrieval:
        run_retrieval_tests(questions)

    if args.all or args.pipeline is not None:
        n = args.pipeline if args.pipeline else 50
        run_pipeline_tests(questions, n_sample=n)

    if args.all or args.report:
        print_report()


if __name__ == "__main__":
    main()

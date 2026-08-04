from groq import Groq, RateLimitError
from dotenv import load_dotenv
import os
import json
import time

from app.services import rate_limit_status

load_dotenv()
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5


def _call_llm(prompt: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            raw = client.chat.completions.with_raw_response.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            rate_limit_status.record_from_headers(raw.headers)
            response = raw.parse()
            return response.choices[0].message.content
        except RateLimitError as e:
            print(f"Groq rate limit hit, not retrying: {e}", flush=True)
            if e.response is not None:
                rate_limit_status.record_from_headers(e.response.headers)
            rate_limit_status.record_daily_limit(str(e))
            return None
        except Exception as e:
            print(f"Groq Error (attempt {attempt + 1}/{retries}):", e, flush=True)
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
    return None


def classify_query(query: str) -> str:
    """
    Returns one of: simple | multi_part | summarization | out_of_scope
    Falls back to 'simple' on any error.
    """
    prompt = f"""Classify the user query into exactly one category.

Categories:
- simple: a direct factual question answerable from a single passage
- multi_part: contains multiple distinct sub-questions or requires comparing several concepts
- summarization: asks for a summary, overview, key points, or general explanation of content
- out_of_scope: general world knowledge not related to any uploaded document (news, weather, personal advice, etc.), OR anything about the employee/HR database (employees, departments, attendance, leave, payroll, projects)

Query: {query}

Respond with ONLY one word from: simple | multi_part | summarization | out_of_scope"""

    result = _call_llm(prompt, retries=2)
    if result:
        label = result.strip().lower().split()[0]
        if label in ("simple", "multi_part", "summarization", "out_of_scope"):
            return label
    return "simple"


def decompose_query(query: str) -> list[str]:
    """
    Break a complex query into 2-4 simpler sub-questions.
    Falls back to [query] on any error.
    """
    prompt = f"""Break the following complex question into 2-4 simpler, self-contained sub-questions.
Each sub-question should be independently answerable.

Question: {query}

Respond with ONLY a valid JSON array of strings, no explanation.
Example: ["What is X?", "How does Y work?", "What are the benefits of Z?"]"""

    result = _call_llm(prompt, retries=2)
    if result:
        try:
            start = result.find("[")
            end = result.rfind("]") + 1
            if start != -1 and end > start:
                sub_queries = json.loads(result[start:end])
                if isinstance(sub_queries, list) and sub_queries:
                    return [str(q) for q in sub_queries[:4]]
        except (json.JSONDecodeError, ValueError):
            pass
    return [query]


def generate_answer(query: str, chunks: list[str]) -> str:
    if not chunks:
        return "• **No relevant content found**\n\n- No matching passages were retrieved for your query."

    numbered_context = "\n\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = f"""You are an expert AI assistant answering questions strictly from the provided context passages.

CONTEXT PASSAGES:
{numbered_context}

QUESTION:
{query}

RULES:
1. Answer ONLY using information from the context passages above.
2. If the answer is not in the context, reply exactly: "I could not find the answer in the document."
3. Structure your response with:
   - **Bold headings** for main topics
   - Bullet points (•) for key facts
   - Sub-points (-) for supporting details
4. Keep the answer concise, clear, and professional.
5. Do not invent or infer facts beyond what is stated in the context.

ANSWER:"""

    result = _call_llm(prompt, retries=MAX_RETRIES)
    return result or (
        "• **Error**\n\n"
        "- Unable to generate answer.\n"
        "- Please try again later."
    )


def generate_summary(query: str, chunks: list[str]) -> str:
    if not chunks:
        return "• **No content found**\n\n- No passages were retrieved to summarize."

    numbered_context = "\n\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = f"""You are an expert AI assistant. Provide a comprehensive summary strictly from the context passages below.

CONTEXT PASSAGES:
{numbered_context}

REQUEST:
{query}

RULES:
1. Summarize ONLY from the context — do not add outside knowledge.
2. Use **bold headings** for each major topic or section.
3. Use bullet points (•) for key facts under each heading.
4. Cover all important points in the context.
5. End with a **Key Takeaways** section of 3-5 bullets.

SUMMARY:"""

    result = _call_llm(prompt, retries=MAX_RETRIES)
    return result or (
        "• **Error**\n\n"
        "- Unable to generate summary.\n"
        "- Please try again later."
    )


def synthesize_multi_part(query: str, chunks: list[str], sub_queries: list[str]) -> str:
    if not chunks:
        return "• **No relevant content found**\n\n- No matching passages were retrieved."

    numbered_context = "\n\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)
    )
    sub_q_list = "\n".join(f"- {q}" for q in sub_queries)

    prompt = f"""You are an expert AI assistant. Answer the following multi-part question using ONLY the context passages.

ORIGINAL QUESTION:
{query}

SUB-QUESTIONS TO ADDRESS:
{sub_q_list}

CONTEXT PASSAGES:
{numbered_context}

RULES:
1. Address each sub-question with its own **bold heading**.
2. Use bullet points (•) for details under each sub-question.
3. Answer ONLY from the context — do not invent information.
4. If a sub-question cannot be answered from context, state that explicitly.

ANSWER:"""

    result = _call_llm(prompt, retries=MAX_RETRIES)
    return result or (
        "• **Error**\n\n"
        "- Unable to generate answer.\n"
        "- Please try again later."
    )

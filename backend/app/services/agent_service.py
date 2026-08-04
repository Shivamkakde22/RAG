import json

from groq import BadRequestError, RateLimitError

from app.services.llm_service import client, MODEL
from app.services import rate_limit_status
from app.mcp.hub import mcp_hub

MAX_ITERATIONS = 5
MAX_MALFORMED_TOOL_CALL_RETRIES = 2

SYSTEM_PROMPT = (
    "You are a helpful assistant for a personal document-chat app. "
    "You have tools for querying the user's uploaded documents/database, "
    "the company employee database (employees, departments, attendance, "
    "leave requests, payroll, projects), and a sandboxed workspace file "
    "system. Only use these tools to answer questions about the user's "
    "uploaded documents or the employee database (e.g. listing documents, "
    "document stats, session history, searching document content, employee "
    "details, department headcounts, attendance, leave, payroll, or project "
    "assignments — including salary/payroll analytics such as department "
    "salary stats, top earners, and total monthly payroll cost; "
    "manager/org-chart lookups such as an employee's direct reports or their "
    "manager; attendance rate and leave-balance summaries and who is on "
    "leave on a given date; and recent hires or project staffing). Never "
    "answer from your own general/world knowledge, even "
    "if a tool call fails or returns nothing useful. If the question is not "
    "about the user's uploaded documents or the employee database, or the "
    "tools don't contain the answer, reply with exactly: \"I could not find "
    "the answer in the document.\" "
    "IMPORTANT — currency rule: every single monetary figure you output "
    "(salary, basic_salary, bonus, deductions, net_salary, or any other "
    "amount from the employee database) MUST be prefixed with the ₹ symbol "
    "and comma-formatted, e.g. ₹53,442.38. This applies to every number "
    "everywhere in your answer, including inside lists and tables — never "
    "output a bare number for a money value, and never use $. "
    "Be concise."
)


def run_agentic_chat(query, max_iterations=MAX_ITERATIONS):
    """Runs a bounded tool-calling loop against Groq using whatever MCP tools
    are currently available. Returns None if no tools are available at all,
    so the caller can fall back to the static out-of-scope reply."""
    tools = mcp_hub.list_tools()
    if not tools:
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    tools_used = []

    for _ in range(max_iterations):
        response = None
        for attempt in range(MAX_MALFORMED_TOOL_CALL_RETRIES + 1):
            try:
                raw = client.chat.completions.with_raw_response.create(
                    model=MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                rate_limit_status.record_from_headers(raw.headers)
                response = raw.parse()
                break
            except RateLimitError as e:
                print(f"Agent rate limit hit, not retrying: {e}", flush=True)
                if e.response is not None:
                    rate_limit_status.record_from_headers(e.response.headers)
                rate_limit_status.record_daily_limit(str(e))
                return {
                    "answer": "I'm temporarily rate-limited by the AI provider — please try again in a bit.",
                    "tools_used": tools_used,
                }
            except BadRequestError as e:
                is_malformed_tool_call = (
                    getattr(e, "body", None) is not None
                    and isinstance(e.body, dict)
                    and e.body.get("error", {}).get("code") == "tool_use_failed"
                )
                if is_malformed_tool_call and attempt < MAX_MALFORMED_TOOL_CALL_RETRIES:
                    print(f"Agent malformed tool call, retrying ({attempt + 1}): {e}", flush=True)
                    continue
                print(f"Agent Error: {e}", flush=True)
                return {
                    "answer": "Something went wrong while using the available tools.",
                    "tools_used": tools_used,
                }
            except Exception as e:
                print(f"Agent Error: {e}", flush=True)
                return {
                    "answer": "Something went wrong while using the available tools.",
                    "tools_used": tools_used,
                }

        if response is None:
            return {
                "answer": "Something went wrong while using the available tools.",
                "tools_used": tools_used,
            }

        message = response.choices[0].message

        if not message.tool_calls:
            return {"answer": message.content, "tools_used": tools_used}

        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            try:
                result = mcp_hub.call_tool(name, args)
            except Exception as e:
                result = f"Error calling tool: {e}"

            tools_used.append({"name": name, "arguments": args})

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result if isinstance(result, str) else json.dumps(result, default=str),
                }
            )

    return {
        "answer": "I wasn't able to fully answer that using the available tools.",
        "tools_used": tools_used,
    }

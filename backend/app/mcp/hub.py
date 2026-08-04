import asyncio
import os
import platform
import sys
import threading
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))          # backend/app/mcp
_APP_DIR = os.path.dirname(_THIS_DIR)                            # backend/app
BACKEND_DIR = os.path.dirname(_APP_DIR)                          # backend

_NPX = "npx.cmd" if platform.system() == "Windows" else "npx"


def _server_configs():
    fs_root = os.path.join(BACKEND_DIR, "mcp_workspace")
    os.makedirs(fs_root, exist_ok=True)

    configs = [
        {
            "name": "data",
            "params": StdioServerParameters(
                command=sys.executable,
                args=["-m", "app.mcp.data_server"],
                cwd=BACKEND_DIR,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            ),
        },
        {
            "name": "employee",
            "params": StdioServerParameters(
                command=sys.executable,
                args=["-m", "app.mcp.employee_server"],
                cwd=BACKEND_DIR,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            ),
        },
        {
            "name": "filesystem",
            "params": StdioServerParameters(
                command=_NPX,
                args=["-y", "@modelcontextprotocol/server-filesystem", fs_root],
                cwd=BACKEND_DIR,
            ),
        },
    ]

    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        configs.append(
            {
                "name": "search",
                "params": StdioServerParameters(
                    command=_NPX,
                    args=["-y", "@modelcontextprotocol/server-brave-search"],
                    env={**os.environ, "BRAVE_API_KEY": brave_key},
                    cwd=BACKEND_DIR,
                ),
            }
        )

    return configs


class MCPToolHub:
    """Long-lived MCP client manager. Flask stays sync; this owns a background
    asyncio event loop so MCP server subprocesses/sessions can persist across
    requests instead of being spawned per-call."""

    def __init__(self):
        self._loop = None
        self._thread = None
        self._sessions = {}
        self._tool_owner = {}
        self._tools_schema = []
        self._started = False
        self._stop_event = None
        self._lifespan_future = None
        self._ready = threading.Event()

    def start(self, timeout=60):
        if self._started:
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self._lifespan_future = asyncio.run_coroutine_threadsafe(
            self._lifespan(), self._loop
        )

        if not self._ready.wait(timeout=timeout):
            print("MCP hub: startup timed out")

        self._started = True
        print(f"MCP hub: ready with {len(self._tools_schema)} tools total")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _lifespan(self):
        """Owns the whole session lifetime in a single task: open every server
        context, signal readiness, block until stop() is requested, then let
        the `async with` unwind the same contexts it opened. anyio's cancel
        scopes require enter/exit to happen in the same task, so start/stop
        can't be two independently-scheduled coroutines."""
        self._stop_event = asyncio.Event()

        async with AsyncExitStack() as stack:
            for config in _server_configs():
                name = config["name"]
                try:
                    read, write = await stack.enter_async_context(
                        stdio_client(config["params"])
                    )
                    session = await stack.enter_async_context(
                        ClientSession(read, write)
                    )
                    await session.initialize()
                    tools_result = await session.list_tools()

                    self._sessions[name] = session
                    for tool in tools_result.tools:
                        prefixed = f"{name}__{tool.name}"
                        self._tool_owner[prefixed] = (name, tool.name)
                        self._tools_schema.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": prefixed,
                                    "description": tool.description or "",
                                    "parameters": tool.inputSchema,
                                },
                            }
                        )
                    print(f"MCP hub: '{name}' connected — {len(tools_result.tools)} tools")
                except Exception as e:
                    print(f"MCP hub: '{name}' failed to start, skipping: {e}")

            self._ready.set()
            await self._stop_event.wait()

    def list_tools(self):
        return list(self._tools_schema)

    def call_tool(self, prefixed_name, arguments):
        if not self._started or prefixed_name not in self._tool_owner:
            raise ValueError(f"Unknown or unavailable tool: {prefixed_name}")

        server_name, tool_name = self._tool_owner[prefixed_name]
        session = self._sessions[server_name]

        future = asyncio.run_coroutine_threadsafe(
            session.call_tool(tool_name, arguments or {}), self._loop
        )
        result = future.result(timeout=30)

        if result.structuredContent is not None:
            return result.structuredContent

        text_parts = [c.text for c in result.content if hasattr(c, "text")]
        return "\n".join(text_parts)

    def stop(self):
        if not self._started or self._loop is None:
            return

        self._loop.call_soon_threadsafe(self._stop_event.set)
        try:
            self._lifespan_future.result(timeout=15)
        except Exception as e:
            print(f"MCP hub: shutdown error: {e}")

        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._started = False
        print("MCP hub: stopped")


mcp_hub = MCPToolHub()

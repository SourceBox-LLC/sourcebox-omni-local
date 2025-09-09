import os
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

# Accept either base URL or /healthz; derive /mcp endpoint
BASE = os.environ.get("MCP_HTTP_BASE", "http://127.0.0.1:8765/healthz").strip()
base_norm = BASE.rstrip("/")
if base_norm.endswith("/healthz"):
    ENDPOINT = base_norm[: -len("/healthz")] + "/mcp"
else:
    ENDPOINT = base_norm + "/mcp"

print(f"Testing MCP HTTP at: {ENDPOINT}")

async def main():
    async with streamablehttp_client(ENDPOINT, terminate_on_close=True) as (read, write, get_session_id):
        session = ClientSession(read, write)
        print("Initializing...")
        await session.initialize()
        print("Initialized. Listing tools...")
        tools = await session.list_tools()
        names = [t.name for t in (tools.tools or [])]
        print("Tools:", names)
        print("Calling ping...")
        res = await session.call_tool("ping", {"message": "hello"})
        print("Result:", getattr(res, "content", res))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("FAILED:", repr(e))
        raise

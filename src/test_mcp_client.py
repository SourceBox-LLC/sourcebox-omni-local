import os
import sys
import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Read command and args from env or defaults
CMD = os.environ.get("MCP_TEST_CMD", r"python")
ARG0 = os.environ.get("MCP_TEST_ARG0", r"-u")
ARG1 = os.environ.get("MCP_TEST_ARG1", r"C:\\Users\\S'Bussiso\\Desktop\\Dummy MCP\\dummy_mcp_server\\server.py")
ARGS = [a for a in [ARG0, ARG1] if a]

print(f"Using command: {CMD}")
print(f"Using args: {ARGS}")

async def main():
    params = StdioServerParameters(command=CMD, args=ARGS)
    async with stdio_client(params) as (read, write):
        session = ClientSession(read, write)
        print("Initializing session...")
        init = await session.initialize()
        print("Initialized. Server: ", init.serverInfo if hasattr(init, 'serverInfo') else init)
        tools = await session.list_tools()
        print("Tools:", [t.name for t in tools.tools])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("FAILED:", repr(e))
        raise

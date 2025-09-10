import argparse
import asyncio
import os
import sys
from typing import List

try:
    from mcp.client.stdio import stdio_client, StdioServerParameters
    from mcp.client.session import ClientSession
except Exception as e:
    print(f"ERROR: mcp package not available in this interpreter: {e}")
    sys.exit(1)


def build_args(py: str, script: str, extra: List[str]) -> List[str]:
    args = list(extra or [])
    # ensure script path is present
    if script and (not args or script not in args):
        args.insert(0, script)
    # ensure unbuffered
    if not args or args[0] != "-u":
        args.insert(0, "-u")
    # add stdio mode if not present and a .py path is in args
    has_py = any(str(a).lower().endswith(".py") for a in args)
    has_mode = any(a == "--mode" or (isinstance(a, str) and a.startswith("--mode=")) for a in args)
    if has_py and not has_mode:
        args += ["--mode", "stdio"]
    return args


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--py", required=True, help="Path to python.exe to run the server")
    ap.add_argument("--script", required=True, help="Path to the server.py")
    ap.add_argument("--extra", nargs=argparse.REMAINDER, help="Additional args after --")
    ns = ap.parse_args()

    py = ns.py
    script = ns.script
    extra = ns.extra or []
    if extra and extra[0] == "--":
        extra = extra[1:]

    args = build_args(py, script, extra)
    env = os.environ.copy()
    env.update({
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
        "DUMMY_MCP_LOG_LEVEL": "DEBUG",
    })
    cwd = os.path.dirname(script) if os.path.isabs(script) and os.path.exists(script) else None

    print("Launching:")
    print("  PY:", py)
    print("  ARGS:", args)
    print("  CWD:", cwd)

    import tempfile
    err_f = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False)
    err_path = err_f.name
    try:
        params = StdioServerParameters(command=py, args=args, env=env, cwd=cwd)
        async with stdio_client(params, errlog=err_f) as (read, write):
            session = ClientSession(read, write)
            print("Initializing session (timeout 12s)...")
            await asyncio.wait_for(session.initialize(), timeout=12.0)
            print("Session initialized.")
            tools = await session.list_tools()
            names = [t.name for t in getattr(tools, 'tools', [])]
            print("Tools:", ", ".join(names))
    except BaseException as ex:
        print("FAILED:", repr(ex))
        try:
            err_f.flush(); err_f.close()
        except Exception:
            pass
        try:
            with open(err_path, "r", encoding="utf-8", errors="ignore") as f:
                tail = f.read()[-1000:]
                if tail:
                    print("\nServer stderr (last 1000 chars):\n" + tail)
        except Exception:
            pass
        raise
    finally:
        try:
            err_f.close()
        except Exception:
            pass

if __name__ == "__main__":
    # Use selector policy on Windows to improve stdio pipe compatibility
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(main())

"""Start the MCP server over stdio, list its tools and call one."""
import asyncio, os, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent

async def main():
    env = {**os.environ, "JOBSEARCH_API_KEY": "demo-key", "JOBSEARCH_CLIENT_KEY": "demo-key",
           "PYTHONPATH": str(ROOT / "src")}
    params = StdioServerParameters(command=sys.executable, args=["-m", "jobsearch.mcp_server"], env=env)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("tools:", [t.name for t in tools.tools])
            out = await s.call_tool("score_match", {"job_id": "J001", "my_skills": ["python", "sql"]})
            print(out.content[0].text)

asyncio.run(main())

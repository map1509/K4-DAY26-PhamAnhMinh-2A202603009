"""Verify the running Weather server through MCP, including real API data."""
import asyncio

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8085/mcp",
        httpx_client_factory=lambda **kwargs: httpx.AsyncClient(
            **kwargs, trust_env=False
        ),
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", ", ".join(tool.name for tool in tools.tools))
            for name, args in (
                ("health_check", {}),
                ("get_current_weather", {"city": "Hanoi"}),
                ("get_forecast", {"city": "Danang", "days": 3}),
            ):
                result = await session.call_tool(name, args)
                print(f"\n{name}({args}):")
                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)
                if result.isError:
                    raise RuntimeError(f"MCP tool {name} failed")


if __name__ == "__main__":
    asyncio.run(main())

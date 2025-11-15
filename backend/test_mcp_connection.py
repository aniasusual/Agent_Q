"""
Direct test of MCPTools connection to Playwright MCP server
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from agno.tools.mcp import MCPTools

async def test_mcp_connection():
    print("=" * 60)
    print("Testing MCPTools connection directly")
    print("=" * 60)

    # Create MCPTools instance
    print("\n1. Creating MCPTools instance...")
    mcp_tools = MCPTools(
        command="npx @playwright/mcp@latest --browser chromium",
        transport="stdio",
        timeout_seconds=60,
    )

    print(f"   Created: {mcp_tools}")
    print(f"   Functions: {mcp_tools.functions}")

    # Try to access the internal client
    print("\n2. Checking internal MCP client...")
    if hasattr(mcp_tools, '_client'):
        print(f"   _client exists: {mcp_tools._client}")
    if hasattr(mcp_tools, 'client'):
        print(f"   client exists: {mcp_tools.client}")

    # Check if there's an initialization method
    print("\n3. Looking for initialization methods...")
    methods = [attr for attr in dir(mcp_tools) if not attr.startswith('_')]
    print(f"   Public methods: {methods[:10]}")

    # Try to manually connect if there's a connect method
    if hasattr(mcp_tools, 'connect'):
        print("\n4. Attempting manual connection...")
        try:
            await mcp_tools.connect()
            print("   Connected successfully!")
            print(f"   Functions after connect: {mcp_tools.functions}")
        except Exception as e:
            print(f"   Connection failed: {e}")

    # Try to get tools/functions
    if hasattr(mcp_tools, 'get_tools'):
        print("\n5. Attempting to get tools...")
        try:
            tools = await mcp_tools.get_tools() if asyncio.iscoroutinefunction(mcp_tools.get_tools) else mcp_tools.get_tools()
            print(f"   Tools: {tools}")
        except Exception as e:
            print(f"   Get tools failed: {e}")

    # Check the functions property again
    print("\n6. Final state:")
    print(f"   Functions: {mcp_tools.functions}")
    print(f"   Functions count: {len(mcp_tools.functions) if mcp_tools.functions else 0}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
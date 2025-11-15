"""
Test script to verify MCPTools connection and available functions
"""
import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=backend_dir / ".env")

from app.agents.mainAgent import get_main_agent

async def test_mcp_tools():
    print("=" * 60)
    print("Testing MCPTools initialization and connection")
    print("=" * 60)

    # Create agent
    print("\n1. Creating agent...")
    agent = get_main_agent(
        project_id="test",
        access_token="test_token"
    )

    # Check tools before running
    print("\n2. Tools available:")
    for tool in agent.tools:
        print(f"   - Tool: {tool}")
        if hasattr(tool, 'functions') and tool.functions:
            print(f"     Tool count: {len(tool.functions)}")
            tool_names = list(tool.functions.keys())[:5]
            print(f"     Sample tools: {tool_names}")
            if len(tool.functions) > 5:
                print(f"     ... and {len(tool.functions) - 5} more")

    # Run agent with a test query using async arun()
    print("\n3. Running agent with test query...")
    try:
        response = await agent.arun(
            "List all the browser automation tools you have access to. Give me just the tool names.",
            stream=False
        )
        print(f"\n4. Agent Response:")
        print(f"   {response.content if hasattr(response, 'content') else response}")
    except Exception as e:
        print(f"\n4. Error during agent.arun(): {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
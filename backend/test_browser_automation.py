"""
Test script to verify browser automation with Playwright MCP
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

async def test_browser_automation():
    print("=" * 60)
    print("Testing Browser Automation with Playwright MCP")
    print("=" * 60)

    # Create agent
    print("\n1. Creating agent...")
    agent = get_main_agent(
        project_id="test",
        access_token="test_token",
        debug_mode=True
    )

    # Test 1: Navigate to a website and take a screenshot
    print("\n2. Test: Navigate to example.com and take a screenshot...")
    try:
        response = await agent.arun(
            "Navigate to https://example.com and take a screenshot. Then tell me what you see on the page.",
            stream=False
        )
        print(f"\n   Agent Response:")
        print(f"   {response.content if hasattr(response, 'content') else response}")
    except Exception as e:
        print(f"\n   Error: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Get page snapshot
    print("\n3. Test: Get accessibility snapshot of the page...")
    try:
        response = await agent.arun(
            "Take an accessibility snapshot of the current page and describe the main elements.",
            stream=False
        )
        print(f"\n   Agent Response:")
        print(f"   {response.content if hasattr(response, 'content') else response}")
    except Exception as e:
        print(f"\n   Error: {e}")

    print("\n" + "=" * 60)
    print("Browser automation test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_browser_automation())

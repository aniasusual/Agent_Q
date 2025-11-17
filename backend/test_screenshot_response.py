"""
Test script to see what Playwright MCP returns when taking a screenshot
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.agents.mainAgent import get_main_agent

async def test_screenshot():
    # Set environment variables if needed
    project_id = "test_project"
    access_token = "test_token"

    print("Creating agent...")
    agent = get_main_agent(
        project_id=project_id,
        access_token=access_token,
        debug_mode=True
    )

    print("\nSending screenshot request...")
    message = "Navigate to https://example.com and take a screenshot"

    response = await agent.arun(message, stream=False)

    print("\n" + "="*80)
    print("RESPONSE ANALYSIS")
    print("="*80)
    print(f"\nResponse type: {type(response)}")
    print(f"\nResponse attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")

    if hasattr(response, 'content'):
        content = response.content
        print(f"\nContent type: {type(content)}")
        print(f"Content length: {len(content)}")
        print(f"\nFirst 1000 characters of content:")
        print(content[:1000])
        print("\n...")
        print(f"\nLast 500 characters of content:")
        print(content[-500:])

        # Check for base64 patterns
        import re
        base64_pattern = r'data:image/(?:png|jpeg|jpg);base64,([A-Za-z0-9+/=]+)'
        matches = list(re.finditer(base64_pattern, content))
        print(f"\nFound {len(matches)} base64 image patterns")
        if matches:
            for i, match in enumerate(matches):
                print(f"  Match {i+1}: Position {match.start()}-{match.end()}, Base64 length: {len(match.group(1))}")

        # Check for file paths
        file_pattern = r'file://([^\s\)]+\.(?:png|jpg|jpeg))'
        file_matches = list(re.finditer(file_pattern, content))
        print(f"\nFound {len(file_matches)} file path patterns")
        if file_matches:
            for i, match in enumerate(file_matches):
                print(f"  Match {i+1}: {match.group(0)}")

    if hasattr(response, 'images'):
        print(f"\nResponse.images: {response.images}")

    if hasattr(response, 'files'):
        print(f"\nResponse.files: {response.files}")

    if hasattr(response, 'messages'):
        print(f"\nResponse.messages: {response.messages}")

    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_screenshot())

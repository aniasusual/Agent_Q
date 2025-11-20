import os
from typing import Optional

from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.mongo import MongoDb
from agno.tools.mcp import MCPTools
from agno.tools.user_control_flow import UserControlFlowTools

from ..prompts.mainAgent import SYSTEM_PROMPT

db_url = os.getenv("MONGODB_URL")
print("querying db_url: ", db_url)

db = MongoDb(db_url=db_url)


def get_main_agent(
    model_id: str = "gemini-2.0-flash",
    debug_mode: bool = True,
    project_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Agent:
    """
    Create and return the main Agent with Playwright MCP tools for browser automation.

    The agent has access to 22+ browser automation tools including:
    - Navigation: browser_navigate, browser_navigate_back, browser_tabs
    - Interaction: browser_click, browser_type, browser_fill_form, browser_hover
    - Data extraction: browser_snapshot, browser_take_screenshot
    - JavaScript execution: browser_evaluate, browser_run_code
    - And more...

    Note: MCPTools are async and require using agent.arun() or agent.aprint_response()
    instead of agent.run() or agent.print_response().
    """
    if not project_id or not access_token:
        raise ValueError("project_id and access_token are required to initialize the main agent")

    # Initialize Playwright MCP tools
    # The MCP server will connect lazily on first use
    # See: https://github.com/microsoft/playwright-mcp
    mcp_tools = MCPTools(
        command="npx @playwright/mcp@latest --browser chromium",
        transport="stdio",
        timeout_seconds=60,  # Longer timeout for browser startup
    )

    # Initialize User Control Flow Tools for Human-in-the-Loop
    # This allows the agent to request clarification from users when needed
    user_control_tools = UserControlFlowTools()

    if debug_mode:
        print(f"[DEBUG] Initialized MCPTools for Playwright browser automation")
        print(f"[DEBUG] Initialized UserControlFlowTools for human-in-the-loop")
        print(f"[DEBUG] Tools will connect on first agent.arun() call")

    return Agent(
        model=Gemini(id=model_id),
        tools=[mcp_tools, user_control_tools],
        markdown=True,
        description=SYSTEM_PROMPT,
        # Session and history management
        add_history_to_context=True,     # Automatically include previous messages
        num_history_runs=5,                # Include last 5 conversation turns
        read_chat_history=True,           # Give agent ability to read history
        search_session_history=True,      # Enable cross-session context retrieval
        num_history_sessions=2,           # Search across 2 most recent sessions
        db=db,
        # Memory features
        enable_user_memories=True,
        enable_agentic_memory=True,
        # Session summaries for long conversations
        enable_session_summaries=True,
        # Storage optimization - store everything for debugging
        store_media=True,                 # Store images from screenshots
        store_tool_messages=True,         # Store tool execution details
        store_history_messages=True,      # Store conversation history
        debug_mode=True,
    )

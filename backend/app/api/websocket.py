"""
WebSocket endpoint for real-time communication between extension and backend
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import re
import os
from datetime import datetime

from ..agents.mainAgent import get_main_agent
from ..core.cloudinary_utils import upload_screenshot_base64, upload_screenshot_file
from agno.agent import Agent

router = APIRouter()


def extract_playwright_code(content: str) -> str:
    """
    Extract Playwright code from markdown code blocks in the agent's response.
    Looks for ```playwright code blocks.
    """
    import re

    # Pattern to match ```playwright code blocks
    pattern = r'```playwright\s*\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        # Return the last code block (most recent)
        return matches[-1].strip()

    # Fallback: try to match any TypeScript/JavaScript code block
    pattern = r'```(?:typescript|javascript|ts|js)?\s*\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        for code in reversed(matches):
            # Check if it looks like Playwright code
            if 'test(' in code or '@playwright/test' in code or 'page.' in code:
                return code.strip()

    return ""


class ConnectionManager:
    """Manages WebSocket connections from browser extensions"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_sessions: Dict[str, Agent] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"[WebSocket] Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agent_sessions:
            del self.agent_sessions[client_id]
        print(f"[WebSocket] Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    def get_or_create_agent(self, client_id: str, project_id: str, access_token: str) -> Agent:
        """Get existing agent session or create a new one"""
        if client_id not in self.agent_sessions:
            self.agent_sessions[client_id] = get_main_agent(
                project_id=project_id,
                access_token=access_token,
                debug_mode=False
            )
        return self.agent_sessions[client_id]


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication with browser extension.

    Message format from extension:
    {
        "type": "chat_message",
        "message": "user message text",
        "project_id": "project_id",
        "access_token": "access_token"
    }

    Message format to extension:
    {
        "type": "agent_response" | "agent_thinking" | "error" | "connected" | "screenshot" | "code_generated",
        "content": "response text",
        "timestamp": "ISO timestamp",
        "imageUrl": "optional image URL for screenshots",
        "imageCaption": "optional caption for screenshots",
        "code": "optional Playwright code"
    }
    """
    await manager.connect(websocket, client_id)

    try:
        await manager.send_message(client_id, {
            "type": "connected",
            "content": "Connected to Agent_Q backend",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            message_type = message_data.get("type")

            if message_type == "chat_message":
                await handle_chat_message(client_id, message_data)
            elif message_type == "ping":
                await manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await manager.send_message(client_id, {
                    "type": "error",
                    "content": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"[WebSocket] Error for client {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_chat_message(client_id: str, message_data: dict):
    """Handle incoming chat messages and route to agent"""
    user_message = message_data.get("message", "")
    project_id = message_data.get("project_id", "default")
    access_token = message_data.get("access_token", "default")

    if not user_message:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "Empty message received",
            "timestamp": datetime.now().isoformat()
        })
        return

    try:
        await manager.send_message(client_id, {
            "type": "agent_thinking",
            "content": "Processing your request...",
            "timestamp": datetime.now().isoformat()
        })

        agent = manager.get_or_create_agent(client_id, project_id, access_token)
        # Use client_id as session_id to maintain conversation history
        response = await agent.arun(user_message, stream=False, session_id=client_id)

        response_content = response.content if hasattr(response, 'content') else str(response)

        # Debug: Log response structure
        print(f"\n{'='*80}")
        print(f"[DEBUG] Response type: {type(response)}")

        # Check if response has messages with images
        if hasattr(response, 'messages') and response.messages:
            print(f"[DEBUG] Response has {len(response.messages)} messages")
            for idx, msg in enumerate(response.messages):
                print(f"[DEBUG] Message {idx}: role={msg.role if hasattr(msg, 'role') else 'unknown'}")
                if hasattr(msg, 'images') and msg.images:
                    print(f"[DEBUG] Message {idx} has {len(msg.images)} images")
                    for img_idx, img in enumerate(msg.images):
                        print(f"[DEBUG]   Image {img_idx}: type={type(img)}, attributes={[a for a in dir(img) if not a.startswith('_')][:10]}")
        print(f"{'='*80}\n")

        # Extract screenshots from agent messages
        screenshots = []

        # Check messages for images
        if hasattr(response, 'messages') and response.messages:
            for msg_idx, msg in enumerate(response.messages):
                if hasattr(msg, 'images') and msg.images:
                    for img_idx, img in enumerate(msg.images):
                        try:
                            # Images are agno Image objects with content as bytes
                            if hasattr(img, 'content') and img.content:
                                print(f"[DEBUG] Processing image {img_idx} from message {msg_idx}")
                                print(f"[DEBUG] Image content type: {type(img.content)}, length: {len(img.content) if img.content else 0}")

                                # Convert bytes to base64
                                import base64
                                base64_data = base64.b64encode(img.content).decode('utf-8')
                                print(f"[DEBUG] Converted to base64, length: {len(base64_data)}")

                                # Upload to Cloudinary
                                upload_result = upload_screenshot_base64(base64_data)
                                screenshots.append({
                                    "url": upload_result["url"],
                                    "width": upload_result.get("width"),
                                    "height": upload_result.get("height")
                                })
                                print(f"[Cloudinary] Screenshot uploaded: {upload_result['url']}")
                        except Exception as e:
                            print(f"[Cloudinary] Failed to upload screenshot: {e}")
                            import traceback
                            traceback.print_exc()

        # Send screenshots as separate messages
        for idx, screenshot in enumerate(screenshots):
            await manager.send_message(client_id, {
                "type": "screenshot",
                "content": f"Screenshot {idx + 1}",
                "imageUrl": screenshot["url"],
                "imageCaption": f"Screenshot captured ({screenshot.get('width')}x{screenshot.get('height')})",
                "timestamp": datetime.now().isoformat()
            })

        # Extract Playwright code from response
        playwright_code = extract_playwright_code(response_content)
        if playwright_code:
            print(f"[Code Generation] Extracted {len(playwright_code)} characters of Playwright code")
            await manager.send_message(client_id, {
                "type": "code_generated",
                "content": "Playwright code generated",
                "code": playwright_code,
                "timestamp": datetime.now().isoformat()
            })

        # Send the agent response
        await manager.send_message(client_id, {
            "type": "agent_response",
            "content": response_content,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[Agent] Error processing message for client {client_id}: {e}")
        import traceback
        traceback.print_exc()

        await manager.send_message(client_id, {
            "type": "error",
            "content": f"Failed to process message: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

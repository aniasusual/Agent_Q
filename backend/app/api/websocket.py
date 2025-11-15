"""
WebSocket endpoint for real-time communication between extension and backend
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
from datetime import datetime

from ..agents.mainAgent import get_main_agent
from agno.agent import Agent

router = APIRouter()


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
        "type": "agent_response" | "agent_thinking" | "error" | "connected",
        "content": "response text",
        "timestamp": "ISO timestamp"
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
        response = await agent.arun(user_message, stream=False)

        response_content = response.content if hasattr(response, 'content') else str(response)

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

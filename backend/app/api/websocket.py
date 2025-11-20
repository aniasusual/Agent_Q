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


def remove_playwright_code_blocks(content: str) -> str:
    """
    Remove ```playwright code blocks from the content to avoid showing them in chat.
    """
    import re

    # Remove ```playwright code blocks
    pattern = r'```playwright\s*\n.*?\n```'
    content = re.sub(pattern, '', content, flags=re.DOTALL)

    # Clean up extra newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


class ConnectionManager:
    """Manages WebSocket connections from browser extensions"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_sessions: Dict[str, Agent] = {}
        self.paused_runs: Dict[str, any] = {}  # Store paused run states for HITL

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
        if client_id in self.paused_runs:
            del self.paused_runs[client_id]
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

    Message formats from extension:
    1. Chat message:
    {
        "type": "chat_message",
        "message": "user message text",
        "project_id": "project_id",
        "access_token": "access_token"
    }

    2. User input response (for HITL):
    {
        "type": "user_input_response",
        "inputs": {
            "field_name": "field_value",
            ...
        }
    }

    3. Run code:
    {
        "type": "run_code",
        "code": "Playwright code to execute",
        "project_id": "project_id",
        "access_token": "access_token"
    }

    Message formats to extension:
    1. Standard responses:
    {
        "type": "agent_response" | "agent_thinking" | "agent_response_chunk" | "error" | "connected",
        "content": "response text",
        "timestamp": "ISO timestamp"
    }

    2. Screenshot:
    {
        "type": "screenshot",
        "content": "Screenshot captured",
        "imageUrl": "cloudinary URL",
        "imageCaption": "screenshot caption",
        "timestamp": "ISO timestamp"
    }

    3. Code generated:
    {
        "type": "code_generated",
        "content": "Playwright code generated",
        "code": "Playwright test code",
        "timestamp": "ISO timestamp"
    }

    4. User input request (HITL):
    {
        "type": "user_input_request",
        "content": "The agent needs additional information to proceed",
        "fields": [
            {
                "name": "field_name",
                "description": "field description",
                "field_type": "string | number | boolean",
                "required": true
            }
        ],
        "timestamp": "ISO timestamp"
    }

    5. Code execution result:
    {
        "type": "code_execution_result" | "code_execution_started",
        "content": "execution status",
        "success": true | false,
        "output": "execution output",
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
            elif message_type == "run_code":
                await handle_run_code(client_id, message_data)
            elif message_type == "user_input_response":
                await handle_user_input_response(client_id, message_data)
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
        # Use project_id as user_id and client_id as session_id for proper session management
        # This allows multiple sessions per user (project) while maintaining isolation

        # Enable streaming with events to get tool completion events with images
        # stream_events=True is required to receive ToolCallCompletedEvent with MCP tool images
        response_stream = agent.arun(
            user_message,
            stream=True,
            stream_events=True,  # CRITICAL: Required for tool responses with images
            user_id=project_id,      # Isolate conversations by project
            session_id=client_id     # Maintain conversation history per client
        )

        # Stream the response and process images in real-time
        full_response_content = ""
        processed_image_ids = set()  # Track processed images to avoid duplicates
        run_response = None  # Store the final run response for HITL

        async for chunk in response_stream:
            # Store the chunk as potential run_response (last chunk will be the final response)
            run_response = chunk

            # Debug: Log chunk type
            chunk_type = type(chunk).__name__
            print(f"[DEBUG] Chunk type: {chunk_type}")

            # Handle ToolCallCompletedEvent for tool responses with images
            if chunk_type == 'ToolCallCompletedEvent':
                print(f"[DEBUG] ToolCallCompletedEvent detected!")
                print(f"[DEBUG] Has images: {hasattr(chunk, 'images') and chunk.images is not None}")

                # Process images from tool completion
                if hasattr(chunk, 'images') and chunk.images:
                    images = chunk.images
                    print(f"[DEBUG] Found {len(images)} images in ToolCallCompletedEvent")

                    for img_idx, image in enumerate(images):
                        # Create unique ID for this image
                        img_id = id(image)

                        if img_id in processed_image_ids:
                            print(f"[DEBUG] Skipping duplicate image {img_id}")
                            continue

                        processed_image_ids.add(img_id)
                        print(f"[DEBUG] Processing image {img_idx}: type={type(image)}")

                        try:
                            import base64

                            # Handle image content or URL
                            if hasattr(image, 'content') and image.content:
                                # Image has bytes content
                                image_bytes = image.content
                                if isinstance(image_bytes, bytes):
                                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                                elif isinstance(image_bytes, str):
                                    base64_data = image_bytes
                                else:
                                    print(f"[DEBUG] Unknown image content type: {type(image_bytes)}")
                                    continue

                                print(f"[DEBUG] Uploading screenshot to Cloudinary...")
                                upload_result = upload_screenshot_base64(base64_data)

                                # Send screenshot immediately
                                await manager.send_message(client_id, {
                                    "type": "screenshot",
                                    "content": "Screenshot captured",
                                    "imageUrl": upload_result["url"],
                                    "imageCaption": f"Screenshot ({upload_result.get('width')}x{upload_result.get('height')})",
                                    "timestamp": datetime.now().isoformat()
                                })
                                print(f"[Cloudinary] Screenshot uploaded and sent: {upload_result['url']}")

                            elif hasattr(image, 'url') and image.url:
                                # Image has URL
                                print(f"[DEBUG] Image has URL: {image.url}")
                                await manager.send_message(client_id, {
                                    "type": "screenshot",
                                    "content": "Screenshot captured",
                                    "imageUrl": image.url,
                                    "imageCaption": "Screenshot",
                                    "timestamp": datetime.now().isoformat()
                                })
                                print(f"[DEBUG] Screenshot URL sent: {image.url}")

                        except Exception as e:
                            print(f"[Cloudinary] Failed to process image: {e}")
                            import traceback
                            traceback.print_exc()

            # Handle RunContentEvent for text streaming
            elif chunk_type == 'RunContentEvent':
                # Stream text content
                if hasattr(chunk, 'content') and chunk.content:
                    full_response_content += chunk.content
                    await manager.send_message(client_id, {
                        "type": "agent_response_chunk",
                        "content": chunk.content,
                        "timestamp": datetime.now().isoformat()
                    })

            # Legacy fallback: Check for images directly on the chunk
            if hasattr(chunk, 'images') and chunk.images and chunk_type != 'ToolCallCompletedEvent':
                images = chunk.images
                if isinstance(images, list):
                    print(f"[DEBUG] Chunk has {len(images)} images")
                    for img_idx, image_response in enumerate(images):
                        # Create unique ID for this image
                        img_id = id(image_response)

                        if img_id in processed_image_ids:
                            print(f"[DEBUG] Skipping duplicate image {img_id}")
                            continue

                        print(f"[DEBUG] Processing image {img_idx}: type={type(image_response)}")

                        # Extract image bytes from image_response.content
                        if hasattr(image_response, 'content') and image_response.content:
                            try:
                                processed_image_ids.add(img_id)

                                import base64

                                # Handle different image content formats
                                image_bytes = image_response.content
                                if isinstance(image_bytes, bytes):
                                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                                elif isinstance(image_bytes, str):
                                    base64_data = image_bytes
                                else:
                                    print(f"[DEBUG] Unknown image content type: {type(image_bytes)}")
                                    continue

                                print(f"[DEBUG] Uploading screenshot to Cloudinary...")
                                upload_result = upload_screenshot_base64(base64_data)

                                # Send screenshot immediately as it arrives
                                await manager.send_message(client_id, {
                                    "type": "screenshot",
                                    "content": "Screenshot captured",
                                    "imageUrl": upload_result["url"],
                                    "imageCaption": f"Screenshot ({upload_result.get('width')}x{upload_result.get('height')})",
                                    "timestamp": datetime.now().isoformat()
                                })
                                print(f"[Cloudinary] Screenshot uploaded and sent: {upload_result['url']}")
                            except Exception as e:
                                print(f"[Cloudinary] Failed to process image: {e}")
                                import traceback
                                traceback.print_exc()

        # Get final response content
        response_content = full_response_content

        # Debug: Log final stats
        print(f"\n{'='*80}")
        print(f"[DEBUG] Total processed images: {len(processed_image_ids)}")
        print(f"[DEBUG] Total response length: {len(response_content)} characters")
        print(f"{'='*80}\n")

        # Check if the agent paused for user input (HITL)
        if run_response and hasattr(run_response, 'is_paused') and run_response.is_paused:
            print(f"[HITL] Agent paused for user input")
            # Store the paused run state
            manager.paused_runs[client_id] = run_response

            # Extract user input fields
            user_input_fields = []

            # Method 1: Check tools_requiring_user_input (correct attribute name)
            if hasattr(run_response, 'tools_requiring_user_input') and run_response.tools_requiring_user_input:
                for tool in run_response.tools_requiring_user_input:
                    # The correct attribute is user_input_schema, not user_input_fields
                    if hasattr(tool, 'user_input_schema'):
                        for field in tool.user_input_schema:
                            if field.value is None:  # Only request fields that need values
                                # Convert field_type to string (it's a Python type object)
                                field_type_str = field.field_type.__name__ if hasattr(field.field_type, '__name__') else str(field.field_type)
                                user_input_fields.append({
                                    "name": field.name,
                                    "description": field.description,
                                    "field_type": field_type_str,
                                    "required": True
                                })
                    # Fallback: check for user_input_fields (in case API differs)
                    elif hasattr(tool, 'user_input_fields'):
                        for field in tool.user_input_fields:
                            if field.value is None:
                                # Convert field_type to string
                                field_type_str = field.field_type.__name__ if hasattr(field.field_type, '__name__') else str(field.field_type)
                                user_input_fields.append({
                                    "name": field.name,
                                    "description": field.description,
                                    "field_type": field_type_str,
                                    "required": True
                                })

            # Method 2: Check direct user_input_schema on run_response
            elif hasattr(run_response, 'user_input_schema') and run_response.user_input_schema:
                for field in run_response.user_input_schema:
                    if field.value is None:
                        # Convert field_type to string
                        field_type_str = field.field_type.__name__ if hasattr(field.field_type, '__name__') else str(field.field_type)
                        user_input_fields.append({
                            "name": field.name,
                            "description": field.description,
                            "field_type": field_type_str,
                            "required": True
                        })

            if user_input_fields:
                print(f"[HITL] Requesting {len(user_input_fields)} user inputs: {user_input_fields}")
                # Send user input request to frontend
                await manager.send_message(client_id, {
                    "type": "user_input_request",
                    "content": "The agent needs additional information to proceed",
                    "fields": user_input_fields,
                    "timestamp": datetime.now().isoformat()
                })
                return  # Don't send normal response, wait for user input
            else:
                print(f"[HITL] WARNING: Agent paused but no user input fields found!")

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

        # Remove code blocks from response content before sending to chat
        clean_response = remove_playwright_code_blocks(response_content)

        # Send the agent response (without code blocks)
        await manager.send_message(client_id, {
            "type": "agent_response",
            "content": clean_response,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[Agent] Error processing message for client {client_id}: {e}")
        import traceback
        traceback.print_exc()

        # Handle rate limit errors with user-friendly message
        error_message = str(e)
        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            error_message = "⚠️ Rate limit exceeded. Please wait a few minutes and try again. If this persists, check your Gemini API quota."
        elif "401" in error_message or "403" in error_message:
            error_message = "⚠️ Authentication error. Please check your Gemini API key."
        else:
            error_message = f"Failed to process message: {str(e)}"

        await manager.send_message(client_id, {
            "type": "error",
            "content": error_message,
            "timestamp": datetime.now().isoformat()
        })


async def handle_user_input_response(client_id: str, message_data: dict):
    """Handle user input responses for HITL and resume agent execution"""
    user_inputs = message_data.get("inputs", {})

    if not user_inputs:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "No user inputs provided",
            "timestamp": datetime.now().isoformat()
        })
        return

    # Check if we have a paused run for this client
    if client_id not in manager.paused_runs:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "No paused agent run found. Please start a new conversation.",
            "timestamp": datetime.now().isoformat()
        })
        return

    try:
        print(f"[HITL] Received user inputs: {user_inputs}")

        # Get the paused run response
        run_response = manager.paused_runs[client_id]

        # Update the user input fields with provided values
        if hasattr(run_response, 'tools_requiring_user_input') and run_response.tools_requiring_user_input:
            for tool in run_response.tools_requiring_user_input:
                # Use user_input_schema (correct attribute name)
                if hasattr(tool, 'user_input_schema'):
                    for field in tool.user_input_schema:
                        if field.name in user_inputs:
                            field.value = user_inputs[field.name]
                            print(f"[HITL] Set field '{field.name}' = '{field.value}'")
                # Fallback to user_input_fields
                elif hasattr(tool, 'user_input_fields'):
                    for field in tool.user_input_fields:
                        if field.name in user_inputs:
                            field.value = user_inputs[field.name]
                            print(f"[HITL] Set field '{field.name}' = '{field.value}'")

        # Notify user that we're resuming
        await manager.send_message(client_id, {
            "type": "agent_thinking",
            "content": "Resuming with your input...",
            "timestamp": datetime.now().isoformat()
        })

        # Get the agent session
        agent = manager.agent_sessions.get(client_id)
        if not agent:
            await manager.send_message(client_id, {
                "type": "error",
                "content": "Agent session not found. Please start a new conversation.",
                "timestamp": datetime.now().isoformat()
            })
            return

        # Continue the agent run with the updated values
        response_stream = agent.continue_run(
            run_response=run_response,
            stream=True,
            stream_events=True
        )

        # Process the continued response (similar to handle_chat_message)
        full_response_content = ""
        processed_image_ids = set()
        continued_run_response = None

        async for chunk in response_stream:
            continued_run_response = chunk
            chunk_type = type(chunk).__name__
            print(f"[DEBUG] Continued run chunk type: {chunk_type}")

            # Handle ToolCallCompletedEvent for screenshots
            if chunk_type == 'ToolCallCompletedEvent':
                if hasattr(chunk, 'images') and chunk.images:
                    images = chunk.images
                    for image in images:
                        img_id = id(image)
                        if img_id in processed_image_ids:
                            continue
                        processed_image_ids.add(img_id)

                        try:
                            import base64
                            if hasattr(image, 'content') and image.content:
                                image_bytes = image.content
                                if isinstance(image_bytes, bytes):
                                    base64_data = base64.b64encode(image_bytes).decode('utf-8')
                                elif isinstance(image_bytes, str):
                                    base64_data = image_bytes
                                else:
                                    continue

                                upload_result = upload_screenshot_base64(base64_data)
                                await manager.send_message(client_id, {
                                    "type": "screenshot",
                                    "content": "Screenshot captured",
                                    "imageUrl": upload_result["url"],
                                    "imageCaption": f"Screenshot ({upload_result.get('width')}x{upload_result.get('height')})",
                                    "timestamp": datetime.now().isoformat()
                                })
                        except Exception as e:
                            print(f"[Cloudinary] Failed to process image: {e}")

            # Handle RunContentEvent for text streaming
            elif chunk_type == 'RunContentEvent':
                if hasattr(chunk, 'content') and chunk.content:
                    full_response_content += chunk.content
                    await manager.send_message(client_id, {
                        "type": "agent_response_chunk",
                        "content": chunk.content,
                        "timestamp": datetime.now().isoformat()
                    })

        # Check if agent paused again (for multi-turn HITL)
        if continued_run_response and hasattr(continued_run_response, 'is_paused') and continued_run_response.is_paused:
            print(f"[HITL] Agent paused again for more input")
            manager.paused_runs[client_id] = continued_run_response

            if hasattr(continued_run_response, 'tools_requiring_user_input') and continued_run_response.tools_requiring_user_input:
                user_input_fields = []
                for tool in continued_run_response.tools_requiring_user_input:
                    # Use user_input_schema (correct attribute name)
                    if hasattr(tool, 'user_input_schema'):
                        for field in tool.user_input_schema:
                            if field.value is None:
                                # Convert field_type to string
                                field_type_str = field.field_type.__name__ if hasattr(field.field_type, '__name__') else str(field.field_type)
                                user_input_fields.append({
                                    "name": field.name,
                                    "description": field.description,
                                    "field_type": field_type_str,
                                    "required": True
                                })
                    # Fallback to user_input_fields
                    elif hasattr(tool, 'user_input_fields'):
                        for field in tool.user_input_fields:
                            if field.value is None:
                                # Convert field_type to string
                                field_type_str = field.field_type.__name__ if hasattr(field.field_type, '__name__') else str(field.field_type)
                                user_input_fields.append({
                                    "name": field.name,
                                    "description": field.description,
                                    "field_type": field_type_str,
                                    "required": True
                                })

                if user_input_fields:
                    await manager.send_message(client_id, {
                        "type": "user_input_request",
                        "content": "The agent needs additional information to proceed",
                        "fields": user_input_fields,
                        "timestamp": datetime.now().isoformat()
                    })
                    return
        else:
            # Clear the paused run since we completed successfully
            if client_id in manager.paused_runs:
                del manager.paused_runs[client_id]

        # Process final response
        response_content = full_response_content

        # Extract Playwright code
        playwright_code = extract_playwright_code(response_content)
        if playwright_code:
            await manager.send_message(client_id, {
                "type": "code_generated",
                "content": "Playwright code generated",
                "code": playwright_code,
                "timestamp": datetime.now().isoformat()
            })

        # Send final response
        clean_response = remove_playwright_code_blocks(response_content)
        await manager.send_message(client_id, {
            "type": "agent_response",
            "content": clean_response,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[HITL] Error processing user input for client {client_id}: {e}")
        import traceback
        traceback.print_exc()

        # Clear the paused run on error
        if client_id in manager.paused_runs:
            del manager.paused_runs[client_id]

        await manager.send_message(client_id, {
            "type": "error",
            "content": f"Failed to process user input: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


async def handle_run_code(client_id: str, message_data: dict):
    """Handle code execution requests"""
    code = message_data.get("code", "")
    project_id = message_data.get("project_id", "default")
    access_token = message_data.get("access_token", "default")

    if not code:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "No code provided for execution",
            "timestamp": datetime.now().isoformat()
        })
        return

    try:
        # Notify execution started
        await manager.send_message(client_id, {
            "type": "code_execution_started",
            "content": "Executing Playwright test...",
            "timestamp": datetime.now().isoformat()
        })

        # Create a temporary directory with proper Playwright setup
        import tempfile
        import subprocess
        import shutil

        # Create temp directory for test execution
        temp_dir = tempfile.mkdtemp(prefix='playwright_test_')
        test_file = os.path.join(temp_dir, 'test.spec.ts')

        # Write the test file
        with open(test_file, 'w') as f:
            f.write(code)

        try:
            # Run Playwright test without requiring config file
            # Use --browser to specify browser directly instead of --project
            result = subprocess.run(
                [
                    'npx',
                    '-y',  # Auto-confirm npx prompts
                    'playwright',
                    'test',
                    test_file,
                    '--headed',
                    '--browser=chromium',  # Use --browser instead of --project
                    '--reporter=list',
                    '--timeout=30000',  # 30 second test timeout
                    '--max-failures=1'   # Stop on first failure
                ],
                capture_output=True,
                text=True,
                timeout=90,  # 90 second overall timeout
                cwd=temp_dir,
                env={**os.environ, 'CI': '0'}  # Disable CI mode
            )

            success = result.returncode == 0
            output = result.stdout if result.stdout else result.stderr

            # Send execution result
            await manager.send_message(client_id, {
                "type": "code_execution_result",
                "content": "Test execution completed" if success else "Test execution failed",
                "success": success,
                "output": output,
                "timestamp": datetime.now().isoformat()
            })

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    except subprocess.TimeoutExpired:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "Test execution timed out (90 seconds limit)",
            "timestamp": datetime.now().isoformat()
        })
        # Clean up temp directory on timeout
        try:
            import shutil
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)
        except:
            pass
    except Exception as e:
        print(f"[Code Execution] Error for client {client_id}: {e}")
        import traceback
        traceback.print_exc()

        await manager.send_message(client_id, {
            "type": "error",
            "content": f"Failed to execute code: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

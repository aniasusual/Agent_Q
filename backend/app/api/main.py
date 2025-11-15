from fastapi import APIRouter
from .websocket import router as websocket_router

api_router = APIRouter()

# Include WebSocket router
api_router.include_router(websocket_router, tags=["websocket"])

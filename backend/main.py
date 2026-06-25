"""FastAPI server for the AI Video Automation Agent."""

import asyncio
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .orchestrator import Orchestrator
from .services.gemini_service import GeminiService
from .utils.config import get_settings
from .utils.file_manager import FileManager

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Automation Agent",
    description="AI-powered video generation from ideas to complete videos",
    version="1.0.0",
)

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")

# Global state
active_tasks: dict[str, dict] = {}
websocket_connections: dict[str, list[WebSocket]] = {}


# --- Request/Response Models ---


class ValidateKeyRequest(BaseModel):
    api_key: str


class ValidateKeyResponse(BaseModel):
    valid: bool
    message: str


class GenerateRequest(BaseModel):
    api_key: str
    idea: str
    language: str = "English"
    music_type: str = "song"
    video_style: str = "realistic"
    lipsync: bool = False


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    steps: dict
    result: Optional[dict] = None
    error: Optional[str] = None


# --- API Endpoints ---


@app.get("/")
async def root():
    """Root endpoint - redirect info."""
    return {
        "name": "AI Video Automation Agent",
        "version": "1.0.0",
        "frontend": "/static/index.html",
        "docs": "/docs",
    }


@app.post("/api/validate-key", response_model=ValidateKeyResponse)
async def validate_key(request: ValidateKeyRequest):
    """Validate a Gemini API key.

    Tests the key by making a simple API request.
    """
    if not request.api_key or request.api_key == "your_key_here":
        return ValidateKeyResponse(
            valid=False,
            message="Please provide a valid API key.",
        )

    is_valid, message = await GeminiService.validate_key(request.api_key)

    return ValidateKeyResponse(valid=is_valid, message=message)


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_video(request: GenerateRequest):
    """Start the video generation pipeline.

    Validates the API key, creates a task, and starts generation
    in the background.
    """
    # Validate inputs
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    if not request.idea or len(request.idea.strip()) < 3:
        raise HTTPException(status_code=400, detail="Please provide a meaningful idea (at least 3 characters)")

    if request.language not in ["Hindi", "English", "Hinglish"]:
        raise HTTPException(status_code=400, detail="Language must be Hindi, English, or Hinglish")

    if request.music_type not in ["song", "voiceover"]:
        raise HTTPException(status_code=400, detail="Music type must be 'song' or 'voiceover'")

    if request.video_style not in ["realistic", "animated", "mixed"]:
        raise HTTPException(status_code=400, detail="Video style must be 'realistic', 'animated', or 'mixed'")

    # Create task
    task_id = str(uuid.uuid4())[:8]

    active_tasks[task_id] = {
        "status": "starting",
        "steps": {},
        "result": None,
        "error": None,
    }

    # Start generation in background
    asyncio.create_task(
        _run_generation(task_id, request)
    )

    return GenerateResponse(
        task_id=task_id,
        status="started",
        message="Video generation pipeline started. Connect to WebSocket for live updates.",
    )


@app.get("/api/status/{task_id}", response_model=TaskStatusResponse)
async def get_status(task_id: str):
    """Get the current status of a generation task."""
    if task_id not in active_tasks:
        # Check if result exists on disk
        file_manager = FileManager()
        if file_manager.task_exists(task_id):
            result = file_manager.load_json(task_id, "pipeline_result.json")
            if result:
                return TaskStatusResponse(
                    task_id=task_id,
                    status=result.get("status", "unknown"),
                    steps=result.get("steps", {}),
                    result=result,
                )

        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        steps=task.get("steps", {}),
        result=task.get("result"),
        error=task.get("error"),
    )


@app.get("/api/download/{task_id}")
async def download_video(task_id: str):
    """Download the generated video for a task.

    Currently returns the script/screenplay JSON as video generation
    is not yet implemented.
    """
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    # For now, return the screenplay JSON (video not yet generated)
    result_path = file_manager.get_task_dir(task_id) / "pipeline_result.json"
    if result_path.exists():
        return FileResponse(
            path=str(result_path),
            filename=f"result_{task_id}.json",
            media_type="application/json",
        )

    raise HTTPException(status_code=404, detail="No output available for this task")


# --- WebSocket Endpoint ---


@app.websocket("/ws/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for live progress updates.

    Clients connect here to receive real-time updates about
    their generation task.
    """
    await websocket.accept()

    # Register connection
    if task_id not in websocket_connections:
        websocket_connections[task_id] = []
    websocket_connections[task_id].append(websocket)

    try:
        # Send initial status
        if task_id in active_tasks:
            await websocket.send_json({
                "type": "status",
                "task_id": task_id,
                "data": active_tasks[task_id],
            })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({"type": "keepalive"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        # Remove connection
        if task_id in websocket_connections:
            websocket_connections[task_id] = [
                ws for ws in websocket_connections[task_id] if ws != websocket
            ]
            if not websocket_connections[task_id]:
                del websocket_connections[task_id]


# --- Background Tasks ---


async def _run_generation(task_id: str, request: GenerateRequest) -> None:
    """Run the generation pipeline in the background.

    Args:
        task_id: Unique task identifier.
        request: Generation request parameters.
    """
    try:
        active_tasks[task_id]["status"] = "in_progress"

        # Create orchestrator
        orchestrator = Orchestrator(request.api_key)

        # Define progress callback
        async def progress_callback(update: dict) -> None:
            """Send progress updates via WebSocket."""
            active_tasks[task_id]["steps"][update.get("step", "")] = update

            # Broadcast to all connected WebSocket clients
            if task_id in websocket_connections:
                message = {
                    "type": "progress",
                    "task_id": task_id,
                    "data": update,
                }
                disconnected = []
                for ws in websocket_connections[task_id]:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        disconnected.append(ws)

                # Clean up disconnected clients
                for ws in disconnected:
                    websocket_connections[task_id].remove(ws)

        # Run the pipeline
        result = await orchestrator.run_pipeline(
            idea=request.idea,
            language=request.language,
            music_type=request.music_type,
            video_style=request.video_style,
            lipsync=request.lipsync,
            task_id=task_id,
            progress_callback=progress_callback,
        )

        active_tasks[task_id]["status"] = result.get("status", "completed")
        active_tasks[task_id]["result"] = result

        # Send completion message
        if task_id in websocket_connections:
            message = {
                "type": "completed",
                "task_id": task_id,
                "data": result,
            }
            for ws in websocket_connections[task_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)

        # Send error message
        if task_id in websocket_connections:
            message = {
                "type": "error",
                "task_id": task_id,
                "data": {"error": str(e)},
            }
            for ws in websocket_connections[task_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

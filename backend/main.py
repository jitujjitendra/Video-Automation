"""FastAPI server for the AI Video Automation Agent."""

import asyncio
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
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


class HealthResponse(BaseModel):
    status: str
    version: str
    active_tasks: int


# --- API Endpoints ---


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        active_tasks=len(active_tasks),
    )


@app.get("/")
async def root():
    """Root endpoint - serve frontend or redirect info."""
    frontend_index = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(str(frontend_index))
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
async def download_video(task_id: str, type: Optional[str] = Query(None)):
    """Download generated assets for a task.

    Query param 'type' can be: video, audio, notebook, all.
    Defaults to the pipeline result JSON.
    """
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    task_dir = file_manager.get_task_dir(task_id)

    if type == "video":
        video_path = task_dir / "final_video.mp4"
        if video_path.exists():
            return FileResponse(
                path=str(video_path),
                filename=f"video_{task_id}.mp4",
                media_type="video/mp4",
            )
        raise HTTPException(status_code=404, detail="Video not available for this task")

    elif type == "audio":
        # Return first available audio file or zip
        audio_dir = task_dir / "audio"
        if audio_dir.exists():
            audio_files = list(audio_dir.glob("*.mp3"))
            if audio_files:
                return FileResponse(
                    path=str(audio_files[0]),
                    filename=audio_files[0].name,
                    media_type="audio/mpeg",
                )
        raise HTTPException(status_code=404, detail="Audio not available for this task")

    elif type == "notebook":
        notebook_path = task_dir / "lipsync_notebook.ipynb"
        if notebook_path.exists():
            return FileResponse(
                path=str(notebook_path),
                filename=f"lipsync_{task_id}.ipynb",
                media_type="application/json",
            )
        raise HTTPException(status_code=404, detail="Notebook not available for this task")

    # Default: return pipeline result JSON
    result_path = task_dir / "pipeline_result.json"
    if result_path.exists():
        return FileResponse(
            path=str(result_path),
            filename=f"result_{task_id}.json",
            media_type="application/json",
        )

    raise HTTPException(status_code=404, detail="No output available for this task")


@app.get("/api/audio/{task_id}/{filename}")
async def stream_audio(task_id: str, filename: str):
    """Stream an audio file for playback."""
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    audio_path = file_manager.get_task_dir(task_id) / "audio" / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename,
    )


@app.get("/api/video/{task_id}")
async def stream_video(task_id: str):
    """Stream the final video for a task."""
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    video_path = file_manager.get_task_dir(task_id) / "final_video.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not available for this task")

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"video_{task_id}.mp4",
    )


@app.get("/api/notebook/{task_id}")
async def download_notebook(task_id: str):
    """Download generated Colab notebook for a task."""
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    notebook_path = file_manager.get_task_dir(task_id) / "lipsync_notebook.ipynb"
    if not notebook_path.exists():
        raise HTTPException(status_code=404, detail="Notebook not available for this task")

    return FileResponse(
        path=str(notebook_path),
        filename=f"lipsync_processing_{task_id}.ipynb",
        media_type="application/json",
    )


@app.get("/api/assets/{task_id}")
async def get_assets(task_id: str):
    """Get list of all generated assets for a task."""
    file_manager = FileManager()
    if not file_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    task_dir = file_manager.get_task_dir(task_id)
    assets = []

    # Check for various asset types
    result_path = task_dir / "pipeline_result.json"
    if result_path.exists():
        assets.append({"type": "result", "filename": "pipeline_result.json", "path": f"/api/download/{task_id}"})

    video_path = task_dir / "final_video.mp4"
    if video_path.exists():
        assets.append({"type": "video", "filename": "final_video.mp4", "path": f"/api/video/{task_id}"})

    notebook_path = task_dir / "lipsync_notebook.ipynb"
    if notebook_path.exists():
        assets.append({"type": "notebook", "filename": "lipsync_notebook.ipynb", "path": f"/api/notebook/{task_id}"})

    audio_dir = task_dir / "audio"
    if audio_dir.exists():
        for audio_file in sorted(audio_dir.glob("*.mp3")):
            assets.append({
                "type": "audio",
                "filename": audio_file.name,
                "path": f"/api/audio/{task_id}/{audio_file.name}",
            })

    return {"task_id": task_id, "assets": assets, "total": len(assets)}


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


# --- Static Files (mounted last to avoid route conflicts) ---

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")

"""
AI Video Automation Agent - Pipeline Test Script

Run with: python -m tests.test_pipeline
Requires: GEMINI_API_KEY environment variable

Tests:
1. Gemini API connection
2. Script generation
3. Edge TTS audio generation
4. FFmpeg availability
5. File management
"""

import os
import sys
import json
import asyncio
import shutil
import tempfile
from pathlib import Path

# Track results
results = []


def log_result(test_name, passed, detail=""):
    """Log a test result."""
    status = "PASS" if passed else "FAIL"
    icon = "[+]" if passed else "[-]"
    results.append({"test": test_name, "passed": passed, "detail": detail})
    print(f"  {icon} {test_name}: {status}")
    if detail and not passed:
        print(f"      Detail: {detail}")


def separator():
    print("-" * 60)


async def test_edge_tts():
    """Test Edge TTS audio generation."""
    try:
        import edge_tts

        # Generate a short audio sample
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        communicate = edge_tts.Communicate(
            "Hello, this is a test of the text to speech system.",
            "en-US-JennyNeural"
        )
        await communicate.save(tmp_path)

        # Check file was created and has content
        file_size = os.path.getsize(tmp_path)
        os.unlink(tmp_path)

        if file_size > 0:
            log_result("Edge TTS - Audio Generation", True,
                       f"Generated {file_size / 1024:.1f} KB audio")
        else:
            log_result("Edge TTS - Audio Generation", False, "Empty audio file")

    except ImportError:
        log_result("Edge TTS - Audio Generation", False, "edge-tts not installed")
    except Exception as e:
        log_result("Edge TTS - Audio Generation", False, str(e))
        # Clean up on error
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def test_edge_tts_hindi():
    """Test Edge TTS with Hindi voice."""
    try:
        import edge_tts

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        communicate = edge_tts.Communicate(
            "यह एक परीक्षण है।",
            "hi-IN-SwaraNeural"
        )
        await communicate.save(tmp_path)

        file_size = os.path.getsize(tmp_path)
        os.unlink(tmp_path)

        if file_size > 0:
            log_result("Edge TTS - Hindi Voice", True,
                       f"Generated {file_size / 1024:.1f} KB audio")
        else:
            log_result("Edge TTS - Hindi Voice", False, "Empty audio file")

    except Exception as e:
        log_result("Edge TTS - Hindi Voice", False, str(e))
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_gemini_connection():
    """Test Gemini API connection."""
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        log_result("Gemini API - Connection", False,
                   "GEMINI_API_KEY environment variable not set")
        return False

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Respond with only the word: OK")

        if response and response.text:
            log_result("Gemini API - Connection", True,
                       f"Response: {response.text.strip()[:50]}")
            return True
        else:
            log_result("Gemini API - Connection", False, "Empty response")
            return False

    except ImportError:
        log_result("Gemini API - Connection", False,
                   "google-generativeai not installed")
        return False
    except Exception as e:
        log_result("Gemini API - Connection", False, str(e))
        return False


def test_script_generation():
    """Test script generation with Gemini."""
    api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        log_result("Gemini API - Script Generation", False,
                   "GEMINI_API_KEY not set (skipped)")
        return

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = """Create a very short screenplay (2 scenes only) for a test video.
Return ONLY valid JSON:
{
    "title": "Test Video",
    "synopsis": "A brief test",
    "scenes": [
        {
            "scene_number": 1,
            "scene_type": "intro",
            "description": "Opening shot",
            "visual_prompt": "A beautiful sunrise",
            "dialogue": "Hello world",
            "duration_seconds": 5
        }
    ]
}"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)

        if "scenes" in data and len(data["scenes"]) > 0:
            log_result("Gemini API - Script Generation", True,
                       f"Generated '{data.get('title', 'Untitled')}' with {len(data['scenes'])} scenes")
        else:
            log_result("Gemini API - Script Generation", False,
                       "No scenes in response")

    except json.JSONDecodeError as e:
        log_result("Gemini API - Script Generation", False,
                   f"Invalid JSON response: {e}")
    except Exception as e:
        log_result("Gemini API - Script Generation", False, str(e))


def test_ffmpeg():
    """Test FFmpeg availability."""
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path:
        # Get version
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True
        )
        version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
        log_result("FFmpeg - Availability", True, version_line)
    else:
        log_result("FFmpeg - Availability", False,
                   "FFmpeg not found in PATH. Install from https://ffmpeg.org/download.html")


def test_ffprobe():
    """Test FFprobe availability."""
    ffprobe_path = shutil.which("ffprobe")

    if ffprobe_path:
        log_result("FFprobe - Availability", True)
    else:
        log_result("FFprobe - Availability", False,
                   "FFprobe not found (usually installed with FFmpeg)")


def test_file_management():
    """Test file management operations."""
    test_dir = Path(tempfile.mkdtemp())

    try:
        # Test directory creation
        task_dir = test_dir / "test_task" / "outputs"
        task_dir.mkdir(parents=True)

        # Test file writing
        test_file = task_dir / "test.json"
        test_data = {"test": True, "message": "Hello"}
        with open(test_file, "w") as f:
            json.dump(test_data, f)

        # Test file reading
        with open(test_file, "r") as f:
            loaded = json.load(f)

        if loaded == test_data:
            log_result("File Management - Read/Write", True)
        else:
            log_result("File Management - Read/Write", False, "Data mismatch")

        # Test outputs directory
        outputs_dir = Path(__file__).parent.parent / "outputs"
        if outputs_dir.exists():
            log_result("File Management - Outputs Directory", True,
                       str(outputs_dir))
        else:
            log_result("File Management - Outputs Directory", False,
                       f"Directory not found: {outputs_dir}")

    except Exception as e:
        log_result("File Management - Read/Write", False, str(e))
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_imports():
    """Test that all required packages can be imported."""
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pydantic": "Pydantic",
        "dotenv": "python-dotenv",
        "google.generativeai": "Google Generative AI",
        "edge_tts": "Edge TTS",
        "websockets": "WebSockets",
        "aiofiles": "aiofiles",
    }

    for module, name in packages.items():
        try:
            __import__(module)
            log_result(f"Import - {name}", True)
        except ImportError:
            log_result(f"Import - {name}", False, f"Cannot import {module}")


def main():
    """Run all tests."""
    print()
    print("=" * 60)
    print("  AI Video Automation Agent - Pipeline Tests")
    print("=" * 60)
    print()

    # Test 1: Imports
    print("[Test Group 1: Package Imports]")
    test_imports()
    separator()

    # Test 2: Gemini API
    print("[Test Group 2: Gemini API]")
    gemini_ok = test_gemini_connection()
    if gemini_ok:
        test_script_generation()
    else:
        log_result("Gemini API - Script Generation", False,
                   "Skipped (no API connection)")
    separator()

    # Test 3: Edge TTS
    print("[Test Group 3: Edge TTS Audio]")
    asyncio.run(test_edge_tts())
    asyncio.run(test_edge_tts_hindi())
    separator()

    # Test 4: FFmpeg
    print("[Test Group 4: FFmpeg]")
    test_ffmpeg()
    test_ffprobe()
    separator()

    # Test 5: File Management
    print("[Test Group 5: File Management]")
    test_file_management()
    separator()

    # Summary
    print()
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("=" * 60)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print()
        print("  Failed tests:")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['test']}: {r['detail']}")

    print()

    # Exit with error code if any tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

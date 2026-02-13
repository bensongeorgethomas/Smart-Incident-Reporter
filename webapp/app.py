"""
Voice of the People - Web Upload Dashboard + Civic Intelligence
================================================================
FastAPI backend that:
  - Accepts image AND video uploads and sends them to the GCS raw-reports bucket
  - Polls the processed-thumbnails bucket for Vision AI + Civic Intelligence results
  - Serves the processed thumbnail image
  - Returns structured civic analysis reports
  - Serves static frontend files
"""

import os
import io
import json
import time
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from google.cloud import storage

from config import Config

storage_client = storage.Client(project=Config.PROJECT_ID)
app = FastAPI(title="Vision Pipeline Dashboard – Civic Intelligence")

STATIC_DIR = Path(__file__).parent / Config.STATIC_DIR

# Supported upload types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES


# ── API Routes ───────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_media(file: UploadFile = File(...)):
    """Upload an image or video to the raw-reports bucket."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Supported: JPEG, PNG, WebP, GIF, MP4, WebM, MOV",
        )

    # 10 MB limit for images, 50 MB limit for videos
    contents = await file.read()
    is_video = file.content_type in ALLOWED_VIDEO_TYPES
    max_size = 50 * 1024 * 1024 if is_video else 10 * 1024 * 1024
    if len(contents) > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {limit_mb} MB",
        )

    # Generate a unique filename to avoid collisions
    timestamp = int(time.time())
    safe_name = file.filename.replace(" ", "_")
    blob_name = f"{timestamp}_{safe_name}"

    # Upload to GCS
    bucket = storage_client.bucket(Config.RAW_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(contents, content_type=file.content_type)

    return {
        "success": True,
        "filename": blob_name,
        "bucket": Config.RAW_BUCKET,
        "media_type": "video" if is_video else "image",
        "message": f"Uploaded to gs://{Config.RAW_BUCKET}/{blob_name}",
    }


@app.get("/api/status/{filename:path}")
async def check_status(filename: str):
    """Check if the media has been processed and return metadata + civic analysis."""
    base_name = filename.rsplit(".", 1)[0]
    thumb_blob_name = f"thumbnails/{base_name}_thumb.jpg"

    bucket = storage_client.bucket(Config.PROCESSED_BUCKET)
    blob = bucket.blob(thumb_blob_name)

    try:
        blob.reload()
    except Exception:
        return JSONResponse(
            status_code=202,
            content={"processed": False, "message": "Still processing..."},
        )

    metadata = blob.metadata or {}

    # Parse safe_search JSON
    safe_search = {}
    if "safe_search" in metadata:
        try:
            safe_search = json.loads(metadata["safe_search"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Parse labels
    labels = []
    if "vision_labels" in metadata:
        labels = [l.strip() for l in metadata["vision_labels"].split(",") if l.strip()]

    # Parse civic intelligence analysis
    civic_analysis = None
    if "civic_analysis" in metadata:
        try:
            civic_analysis = json.loads(metadata["civic_analysis"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Parse AI authenticity indicators
    ai_indicators = []
    if "ai_indicators" in metadata:
        try:
            ai_indicators = json.loads(metadata["ai_indicators"])
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "processed": True,
        "filename": filename,
        "thumbnail": f"/api/thumbnail/{filename}",
        "media_type": metadata.get("media_type", "image"),
        "top_label": metadata.get("top_label", "N/A"),
        "labels": labels,
        "safe_search": safe_search,
        "is_flagged": metadata.get("is_flagged", "False") == "True",
        "source_file": metadata.get("source_file", ""),
        # Civic Intelligence fields
        "civic_analysis": civic_analysis,
        "incident_type": metadata.get("incident_type", "other"),
        "severity_level": int(metadata.get("severity_level", "0")),
        "severity_label": metadata.get("severity_label", "Unknown"),
        "urgency": metadata.get("urgency", "routine"),
        # Authenticity fields
        "ai_generated": metadata.get("ai_generated", "False") == "True",
        "ai_confidence": metadata.get("ai_confidence", "low"),
        "ai_recommendation": metadata.get("ai_recommendation", "accept"),
        "ai_indicators": ai_indicators,
    }


@app.get("/api/analysis/{filename:path}")
async def get_analysis(filename: str):
    """Return just the civic intelligence report as structured JSON."""
    base_name = filename.rsplit(".", 1)[0]
    thumb_blob_name = f"thumbnails/{base_name}_thumb.jpg"

    bucket = storage_client.bucket(Config.PROCESSED_BUCKET)
    blob = bucket.blob(thumb_blob_name)

    try:
        blob.reload()
    except Exception:
        raise HTTPException(status_code=404, detail="Analysis not found")

    metadata = blob.metadata or {}

    if "civic_analysis" not in metadata:
        raise HTTPException(
            status_code=404,
            detail="Civic analysis not available for this file",
        )

    try:
        analysis = json.loads(metadata["civic_analysis"])
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=500, detail="Failed to parse civic analysis")

    return {
        "filename": filename,
        "incident_type": metadata.get("incident_type", "other"),
        "severity_level": int(metadata.get("severity_level", "0")),
        "severity_label": metadata.get("severity_label", "Unknown"),
        "urgency": metadata.get("urgency", "routine"),
        "analysis": analysis,
    }


@app.get("/api/thumbnail/{filename:path}")
async def get_thumbnail(filename: str):
    """Serve the processed thumbnail."""
    base_name = filename.rsplit(".", 1)[0]
    thumb_blob_name = f"thumbnails/{base_name}_thumb.jpg"

    bucket = storage_client.bucket(Config.PROCESSED_BUCKET)
    blob = bucket.blob(thumb_blob_name)

    try:
        image_bytes = blob.download_as_bytes()
    except Exception:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type="image/jpeg",
        headers={"Content-Disposition": f'inline; filename="{base_name}_thumb.jpg"'},
    )


@app.get("/api/history")
async def get_history():
    """List all processed thumbnails with their metadata and civic analysis summaries."""
    bucket = storage_client.bucket(Config.PROCESSED_BUCKET)
    blobs = list(bucket.list_blobs(prefix="thumbnails/"))

    results = []
    for blob in blobs:
        blob.reload()
        metadata = blob.metadata or {}

        safe_search = {}
        if "safe_search" in metadata:
            try:
                safe_search = json.loads(metadata["safe_search"])
            except (json.JSONDecodeError, TypeError):
                pass

        labels = []
        if "vision_labels" in metadata:
            labels = [l.strip() for l in metadata["vision_labels"].split(",") if l.strip()]

        # Extract civic summary (just key fields, not the full report)
        civic_summary = None
        if "civic_analysis" in metadata:
            try:
                full_analysis = json.loads(metadata["civic_analysis"])
                civic_summary = {
                    "scene_description": full_analysis.get("scene_description", ""),
                    "incident_type": full_analysis.get("incident_type", "other"),
                    "severity": full_analysis.get("severity", {}),
                    "urgency": full_analysis.get("public_safety_impact", {}).get(
                        "urgency_label", "routine"
                    ),
                }
            except (json.JSONDecodeError, TypeError):
                pass

        name = blob.name.replace("thumbnails/", "").replace("_thumb.jpg", "")

        results.append({
            "name": name,
            "thumbnail": f"/api/thumbnail/{name}.jpg",
            "media_type": metadata.get("media_type", "image"),
            "top_label": metadata.get("top_label", "N/A"),
            "labels": labels,
            "safe_search": safe_search,
            "is_flagged": metadata.get("is_flagged", "False") == "True",
            "incident_type": metadata.get("incident_type", "other"),
            "severity_level": int(metadata.get("severity_level", "0")),
            "severity_label": metadata.get("severity_label", "Unknown"),
            "civic_summary": civic_summary,
            "created": blob.time_created.isoformat() if blob.time_created else "",
        })

    results.sort(key=lambda x: x["created"], reverse=True)
    return {"images": results}


# ── Serve static frontend (must be LAST) ─────────────────────────────────────

@app.get("/")
async def serve_index():
    """Serve the main page."""
    return FileResponse(STATIC_DIR / "index.html")


# Mount static files for CSS/JS
app.mount("/", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  Smart Incident Reporter – Civic Intelligence Dashboard")
    print(f"  Raw Bucket:       {Config.RAW_BUCKET}")
    print(f"  Processed Bucket: {Config.PROCESSED_BUCKET}")
    print("=" * 60)
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)

"""
Voice of the People – Cloud Function (Gen 2) + Civic Intelligence
==================================================================
Triggered by: google.cloud.storage.object.v1.finalized on the raw-reports bucket.

Pipeline:
  1. Downloads the uploaded image/video from GCS.
  2. Runs Vision AI label_detection + safe_search_detection (images only).
  3. Runs Gemini Pro Vision via the Civic Intelligence Engine for deep analysis.
  4. For images: resizes to 300×300 px thumbnail.
     For videos: extracts a keyframe as thumbnail.
  5. Uploads the thumbnail to the processed-thumbnails bucket with all metadata
     including the full civic intelligence JSON report.
"""

import functions_framework
import os
import io
import json
import logging
import subprocess
import tempfile
from config import Config
from google.cloud import storage, vision
from PIL import Image

from civic_intelligence import CivicIntelligenceEngine

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Initialise clients once (kept warm across cold-start invocations) ────────
storage_client = storage.Client(project=Config.PROJECT_ID)
vision_client = vision.ImageAnnotatorClient()

THUMBNAIL_SIZE = (300, 300)
PROCESSED_BUCKET = Config.PROCESSED_BUCKET

# Civic Intelligence Engine (initialised once for warm starts)
civic_engine = CivicIntelligenceEngine(
    project_id=Config.PROJECT_ID,
    model_name=Config.GEMINI_MODEL,
    location=Config.LOCATION,
)

# SafeSearch likelihood levels
_LIKELIHOOD_NAMES = {
    vision.Likelihood.UNKNOWN: "UNKNOWN",
    vision.Likelihood.VERY_UNLIKELY: "VERY_UNLIKELY",
    vision.Likelihood.UNLIKELY: "UNLIKELY",
    vision.Likelihood.POSSIBLE: "POSSIBLE",
    vision.Likelihood.LIKELY: "LIKELY",
    vision.Likelihood.VERY_LIKELY: "VERY_LIKELY",
}

_SAFE_SEARCH_CATEGORIES = ["adult", "violence", "racy"]
_FLAG_THRESHOLD = {vision.Likelihood.LIKELY, vision.Likelihood.VERY_LIKELY}

# Supported media types
_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_VIDEO_CONTENT_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


def _evaluate_safe_search(safe_search):
    """Return a dict of category → likelihood name AND a boolean flag."""
    results = {}
    flagged = False

    for category in _SAFE_SEARCH_CATEGORIES:
        likelihood = getattr(safe_search, category)
        results[category] = _LIKELIHOOD_NAMES.get(likelihood, "UNKNOWN")
        if likelihood in _FLAG_THRESHOLD:
            flagged = True

    return results, flagged


def _extract_video_keyframe(video_bytes: bytes) -> bytes | None:
    """Extract a keyframe from a video using ffmpeg (available in Cloud Functions).

    Falls back to None if ffmpeg is not available.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
            tmp_in.write(video_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path.replace(".mp4", "_keyframe.jpg")

        subprocess.run(
            [
                "ffmpeg", "-i", tmp_in_path,
                "-vf", "select=eq(n\\,0)",  # Extract first frame
                "-q:v", "2",
                "-frames:v", "1",
                tmp_out_path,
            ],
            capture_output=True,
            timeout=30,
            check=True,
        )

        with open(tmp_out_path, "rb") as f:
            return f.read()

    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        logger.warning("ffmpeg keyframe extraction failed: %s", exc)
        return None
    finally:
        # Cleanup temp files
        for p in [tmp_in_path, tmp_out_path]:
            try:
                os.unlink(p)
            except OSError:
                pass


def _create_thumbnail(image_bytes: bytes) -> bytes:
    """Resize image to 300×300 JPEG thumbnail."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")
    img = img.resize(THUMBNAIL_SIZE, Image.LANCZOS)

    thumb_buffer = io.BytesIO()
    img.save(thumb_buffer, format="JPEG", quality=85)
    thumb_buffer.seek(0)
    return thumb_buffer.read()


@functions_framework.cloud_event
def process_image(cloud_event):
    """Entry-point for the Cloud Function."""

    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    content_type = data.get("contentType", "")

    is_image = content_type in _IMAGE_CONTENT_TYPES
    is_video = content_type in _VIDEO_CONTENT_TYPES

    # ── Guard: only process image/video files ────────────────────────────
    if not is_image and not is_video:
        logger.info("⏭️  Skipping unsupported file: %s (%s)", file_name, content_type)
        return

    media_type = "video" if is_video else "image"
    logger.info("📷 Processing %s: gs://%s/%s", media_type, bucket_name, file_name)

    # ── 1. Download the media from the raw bucket ────────────────────────
    source_bucket = storage_client.bucket(bucket_name)
    source_blob = source_bucket.blob(file_name)
    media_bytes = source_blob.download_as_bytes()
    logger.info("   Downloaded %s bytes", f"{len(media_bytes):,}")

    # ── 2. Vision AI (images only) ───────────────────────────────────────
    label_descriptions = []
    safe_search_results = {}
    is_flagged = False

    if is_image:
        vision_image = vision.Image(content=media_bytes)
        response = vision_client.annotate_image({
            "image": vision_image,
            "features": [
                {"type_": vision.Feature.Type.LABEL_DETECTION, "max_results": 10},
                {"type_": vision.Feature.Type.SAFE_SEARCH_DETECTION},
            ],
        })

        if response.error.message:
            raise RuntimeError(
                f"Vision API error: {response.error.message}\n"
                f"See: https://cloud.google.com/apis/design/errors"
            )

        all_labels = response.label_annotations
        top_3 = all_labels[:3]

        logger.info("🏷️  Top 3 Vision AI Labels:")
        for i, label in enumerate(top_3, start=1):
            logger.info("   %d. %-25s (confidence: %.2f%%)", i, label.description, label.score * 100)

        label_descriptions = [label.description for label in all_labels]

        safe_search = response.safe_search_annotation
        safe_search_results, is_flagged = _evaluate_safe_search(safe_search)

        logger.info("🛡️  SafeSearch Results: %s", json.dumps(safe_search_results))
        if is_flagged:
            logger.warning("🚩 FLAGGED: Image %s contains potentially inappropriate content!", file_name)
        else:
            logger.info("✅ SafeSearch: Image %s passed moderation checks.", file_name)

    # ── 3. Civic Intelligence Analysis (Gemini Pro Vision) ───────────────
    logger.info("🧠 Starting Civic Intelligence analysis...")

    if is_video:
        civic_report = civic_engine.analyze_video(
            video_bytes=media_bytes,
            content_type=content_type,
            vision_labels=label_descriptions if label_descriptions else None,
        )
    else:
        civic_report = civic_engine.analyze_image(
            image_bytes=media_bytes,
            vision_labels=label_descriptions,
            content_type=content_type,
        )

    severity = civic_report.get("severity", {})
    logger.info(
        "🎯 Civic Analysis: type=%s  severity=%s/%s",
        civic_report.get("incident_type", "unknown"),
        severity.get("level", "?"),
        severity.get("label", "?"),
    )
    logger.info(
        "📝 Scene: %s",
        civic_report.get("scene_description", "N/A")[:200],
    )

    # ── Authenticity check is now integrated into analyze_image (Sightengine priority)
    authenticity = civic_report.get("authenticity_assessment", {})

    ai_generated = authenticity.get("is_ai_generated", False)
    ai_confidence = authenticity.get("confidence", "low")
    ai_recommendation = authenticity.get("recommendation", "accept")
    ai_indicators = authenticity.get("indicators", [])

    if ai_generated:
        logger.warning(
            "🤖 AI-GENERATED DETECTED (confidence: %s): %s | Indicators: %s",
            ai_confidence, file_name, ", ".join(ai_indicators),
        )
    else:
        logger.info("✅ Authenticity check passed: image appears genuine.")

    # ── 4. Create thumbnail ──────────────────────────────────────────────
    if is_image:
        thumb_bytes = _create_thumbnail(media_bytes)
    else:
        # Try to extract a keyframe from the video
        keyframe = _extract_video_keyframe(media_bytes)
        if keyframe:
            thumb_bytes = _create_thumbnail(keyframe)
        else:
            # Create a placeholder thumbnail
            placeholder = Image.new("RGB", THUMBNAIL_SIZE, color=(30, 30, 46))
            buf = io.BytesIO()
            placeholder.save(buf, format="JPEG", quality=85)
            buf.seek(0)
            thumb_bytes = buf.read()
            logger.warning("Using placeholder thumbnail (ffmpeg not available)")

    # ── 5. Upload thumbnail with all metadata ────────────────────────────
    dest_bucket = storage_client.bucket(PROCESSED_BUCKET)
    base_name = file_name.rsplit(".", 1)[0]
    thumb_blob_name = f"thumbnails/{base_name}_thumb.jpg"
    dest_blob = dest_bucket.blob(thumb_blob_name)

    # Serialize civic report (GCS metadata values must be strings)
    civic_json = json.dumps(civic_report, ensure_ascii=False)

    dest_blob.metadata = {
        "source_file": f"gs://{bucket_name}/{file_name}",
        "media_type": media_type,
        "vision_labels": ", ".join(label_descriptions) if label_descriptions else "",
        "top_label": label_descriptions[0] if label_descriptions else "N/A",
        "safe_search": json.dumps(safe_search_results),
        "is_flagged": str(is_flagged),
        "civic_analysis": civic_json,
        "incident_type": civic_report.get("incident_type", "other"),
        "severity_level": str(severity.get("level", 0)),
        "severity_label": severity.get("label", "Unknown"),
        "urgency": civic_report.get("public_safety_impact", {}).get("urgency_label", "routine"),
        # Authenticity metadata
        "ai_generated": str(ai_generated),
        "ai_confidence": ai_confidence,
        "ai_recommendation": ai_recommendation,
        "ai_indicators": json.dumps(ai_indicators),
    }

    dest_blob.upload_from_string(thumb_bytes, content_type="image/jpeg")
    logger.info("📤 Thumbnail saved to gs://%s/%s", PROCESSED_BUCKET, thumb_blob_name)
    logger.info("🏁 Processing complete for %s", file_name)


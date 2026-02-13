"""
Civic Intelligence Engine
=========================
Orchestrates the analysis of civic incidents using Gemini Pro Vision and
specialized authenticity detectors.
"""

import logging
import vertexai
from typing import Optional, Dict, Any
from vertexai.generative_models import GenerativeModel, Part

from config import Config
from detectors import AuthenticityDetector
from prompt_templates import IMAGE_ANALYSIS_PROMPT, VIDEO_ANALYSIS_PROMPT, AUTHENTICITY_PROMPT

logger = logging.getLogger(__name__)

# Standard safety settings
from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
_SAFETY_SETTINGS = [
    SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
]

_DEFAULT_REPORT = {
    "scene_description": "Analysis could not be completed.",
    "incident_type": "other",
    "severity": {"level": 0, "label": "Unknown", "justification": "Analysis failed."},
    "authenticity_assessment": {
        "is_ai_generated": False,
        "confidence": "low",
        "indicators": ["Analysis failed"],
        "recommendation": "manual_review",
    },
}

class CivicIntelligenceEngine:
    """Orchestrates structured civic incident reporting."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-2.0-flash",
        zerogpt_api_key: Optional[str] = None,
        **kwargs # Support legacy args like sightengine_user
    ):
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(model_name)
        self.detector = AuthenticityDetector(zerogpt_api_key=zerogpt_api_key)
        
        logger.info(f"🚀 Engine initialized: project={project_id}, model={model_name}")

    def analyze_image(
        self,
        image_bytes: bytes,
        vision_labels: list[str] | None = None,
        content_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        """Runs the full pipeline: Authenticity Check -> Civic Analysis."""
        
        # 1. ZeroGPT Hybrid check (if enabled)
        zerogpt_result = self.detector.check_zerogpt(image_bytes)
        if zerogpt_result and zerogpt_result.get("is_ai"):
            return self._ai_rejection_report(zerogpt_result)

        # 2. Gemini Analysis
        labels_str = ", ".join(vision_labels) if vision_labels else "none detected"
        prompt = IMAGE_ANALYSIS_PROMPT.replace("{vision_labels}", labels_str)
        
        # Include authenticity check in the same Gemini call or separate?
        # The plan was separate for modularity. Let's do the forensic check with Gemini too.
        gemini_auth = self._check_gemini_forensics(image_bytes, content_type)
        
        # 3. Combine Verdicts
        auth_report = self.detector.combine_results(gemini_auth, zerogpt_result)
        
        if auth_report.get("is_ai_generated") and auth_report.get("confidence") == "high":
             return self._ai_rejection_report(auth_report)

        # 4. Final Civic Analysis
        image_part = Part.from_data(data=image_bytes, mime_type=content_type)
        report = self._generate(prompt, image_part)
        
        # Inject the refined authenticity assessment
        report["authenticity_assessment"] = auth_report
        return report

    def analyze_video(self, video_bytes: bytes, content_type: str = "video/mp4", vision_labels: list[str] = None) -> Dict[str, Any]:
        """Analyze video for civic incidents."""
        labels_str = ", ".join(vision_labels) if vision_labels else "none detected"
        prompt = VIDEO_ANALYSIS_PROMPT.replace("{vision_labels}", labels_str)
        video_part = Part.from_data(data=video_bytes, mime_type=content_type)
        return self._generate(prompt, video_part)

    def check_authenticity(self, image_bytes: bytes, content_type: str = "image/jpeg") -> Dict[str, Any]:
        """Backward compatible authenticity check."""
        gemini_auth = self._check_gemini_forensics(image_bytes, content_type)
        zerogpt_result = self.detector.check_zerogpt(image_bytes)
        return self.detector.combine_results(gemini_auth, zerogpt_result)

    def _check_gemini_forensics(self, image_bytes: bytes, content_type: str) -> Dict[str, Any]:
        """Internal forensic check using Gemini."""
        image_part = Part.from_data(data=image_bytes, mime_type=content_type)
        # Use a simpler, faster prompt for just the forensic check
        result = self._generate(AUTHENTICITY_PROMPT, image_part)
        return result

    def _generate(self, prompt: str, media_part: Part) -> Dict[str, Any]:
        """Calls Gemini and parses JSON."""
        try:
            response = self.model.generate_content(
                [media_part, prompt],
                generation_config={"max_output_tokens": 2048, "temperature": 0.1},
                safety_settings=_SAFETY_SETTINGS,
            )
            import json, re
            text = response.text
            # Simple JSON extraction
            match = re.search(r"({.*})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return _DEFAULT_REPORT.copy()

    def _ai_rejection_report(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardized report for AI-detected content."""
        report = _DEFAULT_REPORT.copy()
        report.update({
            "scene_description": "AI-Generated Content Detected.",
            "incident_type": "ai_generated",
            "severity": {"level": 0, "label": "N/A", "justification": "Content is synthetic."},
            "authenticity_assessment": auth_data
        })
        return report
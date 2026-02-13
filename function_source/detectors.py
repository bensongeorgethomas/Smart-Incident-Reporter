import logging
import requests
import json
from typing import Dict, Any, Optional, List
from google.cloud import vision
from vertexai.generative_models import Part, HarmCategory, HarmBlockThreshold, SafetySetting

logger = logging.getLogger(__name__)

class AuthenticityDetector:
    """Handles AI authenticity checks using ZeroGPT and Gemini forensics."""
    
    def __init__(self, zerogpt_api_key: Optional[str] = None):
        self.zerogpt_api_key = zerogpt_api_key
        
    def check_zerogpt(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Check image with ZeroGPT Business API."""
        if not self.zerogpt_api_key:
            return None

        url = "https://api.zerogpt.com/api/detector/detectImage"
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        headers = {"apiKey": self.zerogpt_api_key}

        try:
            response = requests.post(url, files=files, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                return {
                    "is_ai": data.get("is_ai_generated", False),
                    "confidence_score": data.get("ai_score", 0),
                    "provider": "zerogpt"
                }
        except Exception as e:
            logger.error(f"ZeroGPT API error: {e}")
            
        return None

    def combine_results(self, gemini_result: Dict[str, Any], zerogpt_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine Gemini and ZeroGPT results for hybrid verdict."""
        g_is_ai = gemini_result.get("is_ai_generated", False)
        g_conf = gemini_result.get("confidence", "low").lower()
        
        z_is_ai = zerogpt_result.get("is_ai", False) if zerogpt_result else None
        
        verdict = False
        confidence = "low"
        recommendation = "accept"
        indicators = gemini_result.get("indicators", [])

        if z_is_ai is None:
            # Gemini only
            verdict = g_is_ai
            confidence = g_conf
        elif g_is_ai == z_is_ai:
            # Consensus
            verdict = g_is_ai
            confidence = "high"
        else:
            # Disagreement
            verdict = g_is_ai or z_is_ai # Err on side of caution
            confidence = "medium"
            recommendation = "manual_review"
            indicators.append("AI providers disagreed on authenticity")

        if verdict:
            recommendation = "reject" if confidence == "high" else "manual_review"

        return {
            "is_ai_generated": verdict,
            "confidence": confidence,
            "recommendation": recommendation,
            "indicators": indicators,
            "provider_data": {
                "gemini": gemini_result,
                "zerogpt": zerogpt_result
            }
        }

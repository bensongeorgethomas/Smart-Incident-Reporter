import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration for the Vision project."""
    
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "smart-incident-reporter-364cd")
    RAW_BUCKET = os.environ.get("RAW_BUCKET", f"{PROJECT_ID}-raw-reports-bucket")
    PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", f"{PROJECT_ID}-processed-thumbnails-bucket")
    
    # Models
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
    
    # API Keys
    ZEROGPT_API_KEY = os.environ.get("ZEROGPT_API_KEY")
    SIGHTENGINE_USER = os.environ.get("SIGHTENGINE_USER")
    SIGHTENGINE_SECRET = os.environ.get("SIGHTENGINE_SECRET")

    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.PROJECT_ID:
            logger.warning("⚠️ GCP_PROJECT_ID is not set.")
        if not cls.RAW_BUCKET:
            logger.warning("⚠️ RAW_BUCKET is not set.")
        if not cls.PROCESSED_BUCKET:
            logger.warning("⚠️ PROCESSED_BUCKET is not set.")

# Validate on import
Config.validate()

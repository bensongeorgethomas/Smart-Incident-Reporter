import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(dotenv_path="../.env")

class Config:
    """Centralized configuration for the Vision WebApp."""
    
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "smart-incident-reporter-364cd")
    RAW_BUCKET = os.environ.get("RAW_BUCKET", f"{PROJECT_ID}-raw-reports-bucket")
    PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", f"{PROJECT_ID}-processed-thumbnails-bucket")
    
    # Static files
    STATIC_DIR = "static"

    @classmethod
    def validate(cls):
        """Check if buckets are likely valid."""
        if not cls.PROJECT_ID:
             print("⚠️ GCP_PROJECT_ID is not set.")

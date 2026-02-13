import os
import sys
import logging
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add function_source to path so we can import the engine
sys.path.append(str(Path(__file__).parent / "function_source"))

from civic_intelligence import CivicIntelligenceEngine
from prompt_templates import AUTHENTICITY_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "smart-incident-reporter-364cd")
MODEL_NAME = "gemini-2.5-pro"  # Testing the upgraded model
TEST_IMAGE_PATH = "test_cat.jpg"  # Ensure this exists or download it

def main():
    logger.info(f"🚀 Starting Civic Intelligence Verification Test")
    logger.info(f"   Project: {PROJECT_ID}")
    logger.info(f"   Model: {MODEL_NAME}")

    # 1. Initialize Engine
    try:
        engine = CivicIntelligenceEngine(
            project_id=PROJECT_ID, 
            model_name=MODEL_NAME,
            zerogpt_api_key=os.environ.get("ZEROGPT_API_KEY")
        )
        logger.info("✅ CivicIntelligenceEngine initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize engine: {e}")
        return

    # 2. Load Test Image
    if not os.path.exists(TEST_IMAGE_PATH):
        logger.warning(f"⚠️ Test image '{TEST_IMAGE_PATH}' not found. Downloading placeholder...")
        try:
            import urllib.request
            urllib.request.urlretrieve("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg", TEST_IMAGE_PATH)
            logger.info("   Downloaded test_cat.jpg")
        except Exception as e:
            logger.error(f"❌ Failed to download test image: {e}")
            return

    with open(TEST_IMAGE_PATH, "rb") as f:
        image_bytes = f.read()
    
    logger.info(f"📸 Loaded test image ({len(image_bytes)} bytes)")

    # 3. Use dedicated authenticity check
    logger.info("\n🔍 Running Dedicated Authenticity Check (Layer 1 + 2)...")
    try:
        auth_result = engine.check_authenticity(image_bytes, content_type="image/jpeg")
        
        print("\n" + "="*50)
        print(" AUTHENTICITY CHECK RESULTS")
        print("="*50)
        print(f"Is AI Generated? : {auth_result.get('is_ai_generated')}")
        print(f"Confidence       : {auth_result.get('confidence')}")
        print(f"Recommendation   : {auth_result.get('recommendation')}")
        print(f"Image Type       : {auth_result.get('image_type', 'N/A')}")
        print(f"Avg Score        : {auth_result.get('average_score', 'N/A')}")
        print("-" * 20)
        print("SCORES:")
        for k, v in auth_result.get('scores', {}).items():
            print(f"  - {k:<25}: {v}")
        print("-" * 20)
        print("INDICATORS:")
        for ind in auth_result.get('indicators', []):
            print(f"  - {ind}")
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"❌ Authenticity check failed: {e}")

    # 4. Full Analysis (Integration Test)
    logger.info("\n🧠 Running Full Civic Analysis (with Sightengine pre-check)...")
    try:
        # Mock vision labels for context
        mock_labels = ["Cat", "Animal", "Pet", "Street", "Daylight"]
        report = engine.analyze_image(image_bytes, vision_labels=mock_labels, content_type="image/jpeg")
        
        print("\n" + "="*50)
        print(" CIVIC INTELLIGENCE REPORT")
        print("="*50)
        
        # Check for AI Flag
        auth = report.get('authenticity_assessment', {})
        if auth.get('is_ai_generated'):
             print("⚠️ AI-GENERATED CONTENT DETECTED!")
             print(f"Confidence: {auth.get('confidence')}")
        else:
             print("✅ Content appears authentic.")

        print(f"Scene Description: {report.get('scene_description', 'N/A')[:100]}...")
        print(f"Incident Type    : {report.get('incident_type')}")
        
        severity = report.get('severity', {})
        print(f"Severity         : {severity.get('level')}/10 ({severity.get('label')})")
        print(f"Justification    : {severity.get('justification')}")
        
        print("\nRisks:")
        for risk in report.get('predictive_risks', []):
            print(f"  - {risk.get('risk')} ({risk.get('probability')})")
            
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"❌ Full analysis failed: {e}")

if __name__ == "__main__":
    main()

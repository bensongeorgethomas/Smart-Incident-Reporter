"""Quick test to call Sightengine API directly and see what it returns for road.jpeg."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

USER = os.environ.get("SIGHTENGINE_USER")
SECRET = os.environ.get("SIGHTENGINE_SECRET")

print(f"Sightengine User: {USER}")
print(f"Sightengine Secret: {SECRET[:5]}..." if SECRET else "SECRET NOT SET")

if not USER or not SECRET:
    print("❌ Sightengine credentials not found in .env")
    exit(1)

# Read the image
with open("road.jpeg", "rb") as f:
    image_bytes = f.read()

print(f"Image size: {len(image_bytes)} bytes")

# Call Sightengine
files = {'media': ('road.jpeg', image_bytes)}
params = {
    'models': 'genai',
    'api_user': USER,
    'api_secret': SECRET,
}

print("\n🔍 Calling Sightengine API...")
response = requests.post(
    "https://api.sightengine.com/1.0/check.json",
    files=files,
    data=params,
    timeout=30
)

print(f"HTTP Status: {response.status_code}")
result = response.json()
print(f"\n📊 Full Sightengine Response:")
import json
print(json.dumps(result, indent=2))

# Parse the result
if result.get('status') == 'success':
    ai_prob = result.get('type', {}).get('ai_generated', 0.0)
    print(f"\n🎯 AI Generated Probability: {ai_prob:.1%}")
    print(f"   Verdict: {'🤖 AI' if ai_prob >= 0.5 else '✅ REAL'}")
else:
    print(f"\n❌ API Error: {result.get('error')}")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    """Test route to check if the server is running."""
    return {"message": "✅ Server is running on Vercel!"}

class ConvertRequest(BaseModel):
    url: str

@app.post("/convert")
def convert(data: ConvertRequest):
    """Convert a website URL to an unsigned APK."""
    website_url = data.url

    if not website_url:
        raise HTTPException(status_code=400, detail="Missing website URL")

    logging.debug(f"Received URL: {website_url}")

    try:
        sha = trigger_github_action(website_url)
        return {"message": "APK generation triggered successfully. Please check back later for the download link.", "sha": sha}
    except Exception as e:
        logging.error(f"❌ Error triggering APK generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger APK generation: {e}")

def trigger_github_action(website_url):
    url = "https://api.github.com/repos/henryk4god/web-app-converter-backend-main/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}"
    }
    data = {
        "event_type": "build-apk",
        "client_payload": {
            "website_url": website_url
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 204:
        raise Exception(f"Failed to trigger workflow: {response.status_code}")
    return response.headers.get('X-GitHub-Delivery')

@app.get("/status/{sha}")
def check_status(sha: str):
    """Check the status of the APK generation."""
    apk_path = f"/path/to/generated/apks/web_app_converter_{sha}.apk"
    if os.path.exists(apk_path):
        return {"status": "completed", "path": apk_path}
    else:
        return {"status": "pending"}
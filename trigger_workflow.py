import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def trigger_github_action():
    url = "https://api.github.com/repos/henryk4god/web-app-converter-backend-main/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}"
    }
    data = {
        "event_type": "build-apk"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response body: {response.text}")
    if response.status_code == 204:
        print("Workflow triggered successfully")
        return response.headers.get('X-GitHub-Delivery')
    else:
        print(f"Failed to trigger workflow: {response.status_code}")
        return None

sha = trigger_github_action()
print(f"SHA: {sha}")
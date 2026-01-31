import hmac
import hashlib
import json
import requests
import sys
import os

# Add the project root to sys.path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.config import settings
except ImportError:
    print("Error: Could not import settings from src.config. Make sure you are running this from the project root.")
    sys.exit(1)

def send_mock_webhook():
    url = "http://localhost:8000/webhook/github"
    secret = settings.github_webhook_secret
    
    if not secret:
        print("Error: GITHUB_WEBHOOK_SECRET not configured in your settings/.env")
        return

    # Mock payload for a pull request event
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "title": "Test PR for Debugging",
            "user": {"login": "testuser"}
        },
        "repository": {
            "full_name": "owner/repo"
        }
    }
    
    body = json.dumps(payload).encode("utf-8")
    
    # Calculate signature (required by webhook.py)
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": f"sha256={signature}"
    }

    print(f"Sending mock webhook to {url}...")
    try:
        response = requests.post(url, data=body, headers=headers)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        if response.status_code == 200:
            print("\nSuccess! Your debugger should have hit any breakpoints in src/api/webhook.py or GitHubEventHandler.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Did you start the FastAPI server in debug mode? (Press F5 and select 'Python: FastAPI')")

if __name__ == "__main__":
    send_mock_webhook()

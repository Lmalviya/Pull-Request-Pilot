import hmac
import hashlib
import requests
from fastapi import HTTPException
from pydantic import BaseModel
from src.config import settings
from src.services.scm.base import BaseSCM

# --- data models ---

class GitHubUser(BaseModel):
    login: str

class PullRequest(BaseModel):
    title: str
    user: GitHubUser

class Repository(BaseModel):
    full_name: str

class PullRequestEvent(BaseModel):
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository

# --- implementation ---

class GitHubSCM(BaseSCM):
    """
    GitHub implementation of the SCM interface.
    Handles GitHub-specific operations and webhook verification.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.github_base_url
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff"
        }

    @staticmethod
    def verify_signature(body: bytes, signature_header: str) -> bool:
        """
        Verify that the webhook signature matches the expected signature 
        calculated using the secret.
        """
        if not settings.github_webhook_secret:
            raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET not configured")

        if not signature_header:
            return False
        
        expected_prefix = "sha256="
        if not signature_header.startswith(expected_prefix):
            return False
        
        received_signature = signature_header[len(expected_prefix):]
        computed_signature = hmac.new(
            key=settings.github_webhook_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_signature, computed_signature)

    @classmethod
    async def handle_event(cls, event: str, payload: dict):
        """
        Dispatch GitHub webhook events to the appropriate handlers.
        """
        if event == "pull_request":
            pr_event = PullRequestEvent(**payload)
            await cls.handle_pull_request(pr_event)
        elif event == "push":
            cls.handle_push(payload)
        else:
            print(f"Unknown GitHub event: {event}")

    @classmethod
    async def handle_pull_request(cls, pr_event: PullRequestEvent):
        """
        Handle pull request events (e.g., opened, synchronized).
        """
        action = pr_event.action
        pr_number = pr_event.number
        repo_name = pr_event.repository.full_name
        
        print(f"GitHub PR event | action={action} | pr={pr_number} | repo={repo_name}")
        
        if action in ["opened", "synchronize"]:
            # Import here to avoid circular dependencies if ReviewerService imports SCM
            from src.services.reviewer import ReviewerService
            reviewer = ReviewerService()
            await reviewer.review_pull_request(repo_name, pr_number)

    @staticmethod
    def handle_push(payload: dict):
        ref = payload.get("ref")
        print(f"GitHub Push event | ref={ref}")

    def get_pull_request_diff(self, repo_id: str, pr_id: int) -> str:
        """
        Fetch the unified diff of the pull request.
        """
        # To get the diff, usage of the header 'application/vnd.github.v3.diff' 
        # on the PR detail endpoint is required.
        url = f"{self.base_url}/repos/{repo_id}/pulls/{pr_id}"
        
        response = requests.get(url, headers=self.headers, timeout=30)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to fetch diff: {response.text}"
            )
        return response.text

    def post_comment(self, repo_id: str, pr_id: int, body: str) -> bool:
        """
        Post a general comment on the pull request issue.
        """
        # Use the issues endpoint for general conversation comments
        url = f"{self.base_url}/repos/{repo_id}/issues/{pr_id}/comments"
        
        data = {"body": body}
        response = requests.post(url, headers=self.headers, json=data, timeout=30)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return True

    def post_inline_comment(self, repo_id: str, pr_id: int, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of the pull request's diff.
        """
        url = f"{self.base_url}/repos/{repo_id}/pulls/{pr_id}/comments"
        
        # 1. Fetch PR to get head commit sha to ensure comment is attached correctly
        pr_url = f"{self.base_url}/repos/{repo_id}/pulls/{pr_id}"
        json_headers = self.headers.copy()
        if "Accept" in json_headers:
            del json_headers["Accept"] 
        
        commit_id = None
        try:
            pr_resp = requests.get(pr_url, headers=json_headers, timeout=30)
            if pr_resp.status_code == 200:
                commit_id = pr_resp.json().get("head", {}).get("sha")
        except Exception as e:
            print(f"Error fetching PR details: {e}")

        data = {
            "body": body,
            "path": file,
            "line": line,
            "side": "RIGHT"
        }
        if commit_id:
            data["commit_id"] = commit_id

        response = requests.post(url, headers=self.headers, json=data, timeout=30)
        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return True

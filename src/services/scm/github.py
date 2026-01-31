import hmac
import hashlib
from fastapi import HTTPException
from src.config import settings
from pydantic import BaseModel

class GitHubUser(BaseModel):
    login: str

class PullRequest(BaseModel):
    title: str
    user: GitHubUser

class PullRequestEvent(BaseModel):
    action: str
    number: int
    pull_request: PullRequest



class GitHubService:
    @staticmethod
    def verify_signature(body: bytes, signature_header: str) -> bool:
        if not settings.GITHUB_WEBHOOK_SECRET:
            raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET not configured")

        if not signature_header:
            return False
        
        expected_prefix = "sha256="
        if not signature_header.startswith(expected_prefix):
            return False
        
        received_signature = signature_header[len(expected_prefix):]
        computed_signature = hmac.new(
            key=settings.GITHUB_WEBHOOK_SECRET.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_signature, computed_signature)

    @staticmethod
    def handle_event(event: str, payload: dict):
        if event == "pull_request":
            pr_event = PullRequestEvent(**payload)
            GitHubService.handle_pull_request(pr_event)
        elif event == "push":
            GitHubService.handle_push(payload)
        else:
            print(f"Unknown GitHub event: {event}")

    @staticmethod
    def handle_pull_request(pr_event: PullRequestEvent):
        action = pr_event.action
        pr_number = pr_event.number
        print(f"GitHub PR event | action={action} | pr={pr_number}")

    @staticmethod
    def handle_push(payload: dict):
        ref = payload.get("ref")
        print(f"GitHub Push event | ref={ref}")

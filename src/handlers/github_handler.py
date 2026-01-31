from src.models.github_model import PullRequestEvent
from src.services.reviewer import ReviewerService
import hmac
import hashlib
from fastapi import HTTPException
from src.config import settings

class GitHubEventHandler:
    """
    Handles GitHub webhook events and dispatches them to the appropriate services.
    """
    
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
            # Validate payload using our model
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
            reviewer = ReviewerService()
            await reviewer.review_pull_request(repo_name, pr_number)

    @staticmethod
    def handle_push(payload: dict):
        ref = payload.get("ref")
        print(f"GitHub Push event | ref={ref}")

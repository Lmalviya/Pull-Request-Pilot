from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from src.services.scm.github import GitHubService

router = APIRouter(prefix="/webhook")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not GitHubService.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    event = request.headers.get("X-GitHub-Event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    if event == "pull_request":
        action = payload.get("action")
        # Trigger review on opened or synchronized PRs
        if action in ["opened", "synchronize"]:
            background_tasks.add_task(GitHubService.handle_pull_request, payload)
            return {"status": "review_triggered"}
            
    return {"status": "event_ignored"}

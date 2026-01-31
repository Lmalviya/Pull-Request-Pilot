from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from src.handlers.github_handler import GitHubEventHandler

router = APIRouter(prefix="/webhook")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    # Use SCM class for static utility
    if not GitHubEventHandler.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    event = request.headers.get("X-GitHub-Event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    # Delegate all business logic to the event handler
    background_tasks.add_task(GitHubEventHandler.handle_event, event, payload)
    return {"status": "event_received"}

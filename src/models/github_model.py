from pydantic import BaseModel

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
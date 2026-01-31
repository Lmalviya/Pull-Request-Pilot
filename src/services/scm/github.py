import logging
import requests
from fastapi import HTTPException
from src.config import settings
from src.services.scm.base import BaseSCM
from src.code_parser.parser import analysis_file_structure, get_function_content as extract_function_content

# Set up logging
logger = logging.getLogger(__name__)

class GitHubSCM(BaseSCM):
    """
    GitHub implementation of the SCM interface.
    Handles GitHub-specific operations.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.github_base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Pull-Request-Pilot"
        }

    def _request(self, method: str, endpoint: str, accept: str = None, **kwargs) -> requests.Response:
        """
        Internal helper for making GitHub API requests.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.headers.copy()
        if accept:
            headers["Accept"] = accept
            
        try:
            response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            
            # Diagnostic for debugging token permissions if needed
            scopes = response.headers.get("X-OAuth-Scopes")
            if scopes:
                logger.debug(f"GitHub Token Scopes: {scopes}")
                
            if response.status_code not in (200, 201):
                logger.error(f"GitHub API Error [{response.status_code}]: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"GitHub API error: {response.text}"
                )
            return response
        except requests.RequestException as e:
            logger.exception(f"Request to GitHub failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to communicate with GitHub: {str(e)}")

    def get_pull_request(self, repo_id: str, pr_id: int) -> dict:
        """
        Fetch pull request metadata.
        """
        return self._request("GET", f"repos/{repo_id}/pulls/{pr_id}").json()

    def get_pull_request_diff(self, repo_id: str, pr_id: int) -> str:
        """
        Fetch the unified diff of the pull request.
        """
        response = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}", accept="application/vnd.github.v3.diff")
        return response.text

    def get_pull_request_files(self, repo_id: str, pr_id: int) -> list[str]:
        """
        Fetch the list of files changed in a pull request.
        """
        response = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}/files")
        return [f["filename"] for f in response.json()]

    def get_pull_request_file_diffs(self, repo_id: str, pr_id: int) -> list[dict]:
        """
        Fetch the list of files and their diff patches.
        """
        response = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}/files")
        return response.json()

    def get_commit_diff(self, repo_id: str, commit_sha: str) -> str:
        """
        Fetch the unified diff of a specific commit.
        """
        response = self._request("GET", f"repos/{repo_id}/commits/{commit_sha}", accept="application/vnd.github.v3.diff")
        return response.text

    def get_file_structure(self, repo_id: str, file_path: str) -> str:
        """
        Analyze the file content and return a high-level structure/outline.
        """
        content = self.get_file_content(repo_id, file_path)
        return analysis_file_structure(content, file_path)

    def get_file_content(self, repo_id: str, file_path: str, start_line: int = None, end_line: int = None, ref: str = None) -> str:
        """
        Fetch the content of a file. Supports line-level pagination and commit refs.
        """
        endpoint = f"repos/{repo_id}/contents/{file_path}"
        params = {}
        if ref:
            params['ref'] = ref
            
        response = self._request("GET", endpoint, params=params, accept="application/vnd.github.v3.raw")
        content = response.text
        
        if start_line is not None and end_line is not None:
            lines = content.splitlines()
            start_index = max(0, start_line - 1)
            end_index = min(len(lines), end_line)
            return "\n".join(lines[start_index:end_index]) if start_index < len(lines) else ""
            
        return content

    def post_comment(self, repo_id: str, pr_id: int, body: str) -> bool:
        """
        Post a general comment on the pull request issue.
        """
        self._request("POST", f"repos/{repo_id}/issues/{pr_id}/comments", json={"body": body})
        return True

    def post_inline_comment(self, repo_id: str, pr_id: int, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of the pull request's diff.
        """
        # Fetch PR to get head commit sha to ensure comment is attached correctly
        commit_id = None
        try:
            pr_data = self._request("GET", f"repos/{repo_id}/pulls/{pr_id}").json()
            commit_id = pr_data.get("head", {}).get("sha")
        except Exception as e:
            logger.warning(f"Could not fetch PR details for commit_id: {e}")

        data = {
            "body": body,
            "path": file,
            "line": int(line),
            "side": "RIGHT"
        }
        if commit_id:
            data["commit_id"] = commit_id

        logger.debug(f"Posting inline comment to {file}:{line} with commit {commit_id}")
        self._request("POST", f"repos/{repo_id}/pulls/{pr_id}/comments", json=data)
        return True

    def post_commit_inline_comment(self, repo_id: str, commit_sha: str, file: str, line: int, body: str) -> bool:
        """
        Post a comment on a specific line of a commit.
        """
        data = {
            "body": body,
            "path": file,
            "line": line,
            "side": "RIGHT"
        }
        self._request("POST", f"repos/{repo_id}/commits/{commit_sha}/comments", json=data)
        return True

    def get_pull_request_comments(self, repo_id: str, pr_id: int) -> list[dict]:
        """
        Fetch all inline comments on a pull request.
        """
        endpoint = f"repos/{repo_id}/pulls/{pr_id}/comments"
        response = self._request("GET", endpoint)
        return response.json()

    def get_function_content(self, repo_id: str, file_path: str, function_name: str) -> str:
        """
        Fetch the full content of a specific function or class.
        """
        content = self.get_file_content(repo_id, file_path)
        return extract_function_content(content, file_path, function_name)


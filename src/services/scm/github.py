import requests
from fastapi import HTTPException
from src.config import settings
from src.services.scm.base import BaseSCM

from src.code_parser.parser import analysis_file_structure

# --- implementation ---

class GitHubSCM(BaseSCM):
    """
    GitHub implementation of the SCM interface.
    Handles GitHub-specific operations.
    """
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = settings.github_base_url
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff"
        }

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

    def get_file_structure(self, repo_id: str, file_path: str) -> str:
        """
        Analyze the file content and return a high-level structure/outline.
        Currently supports Python files via AST.
        """
        # Fetch the full content to parse structure
        content = self.get_file_content(repo_id, file_path)
        return analysis_file_structure(content, file_path)

    def get_file_content(self, repo_id: str, file_path: str, start_line: int = None, end_line: int = None) -> str:
        """
        Fetch the content of a file. Supports line-level pagination.
        """
        url = f"{self.base_url}/repos/{repo_id}/contents/{file_path}"
        
        # Use a local header copy to request raw content instead of JSON/Diff
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to fetch file content: {response.text}"
            )
            
        content = response.text
        
        # Handle line slicing if requested
        if start_line is not None and end_line is not None:
            lines = content.splitlines()
            # Adjust for 0-based index vs 1-based arguments
            # Ensure indices are within bounds
            start_index = max(0, start_line - 1)
            end_index = min(len(lines), end_line)
            
            if start_index >= len(lines):
                return ""
                
            selected_lines = lines[start_index:end_index]
            return "\n".join(selected_lines)
            
        return content


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

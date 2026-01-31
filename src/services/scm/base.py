from abc import ABC, abstractmethod

class SCMService(ABC):
    @abstractmethod
    def get_pull_request_diff(self, repo_full_name: str, pr_number: int) -> str:
        """Fetch the diff for a pull request."""
        pass

    @abstractmethod
    def post_comment(self, repo_full_name: str, pr_number: int, body: str) -> bool:
        """Post a top-level comment on a pull request."""
        pass

    @abstractmethod
    def post_inline_comment(self, repo_full_name: str, pr_number: int, file: str, line: int, body: str) -> bool:
        """Post an inline comment on a specific file and line."""
        pass
from abc import ABC, abstractmethod

class BaseSCM(ABC):
    @abstractmethod
    def get_pull_request_diff(self, repo_id: str, pr_id: int) -> str:
        """
        Fetch the code diff for a pull request.
        Returns a string representing the diff.
        """
        pass

    @abstractmethod
    def post_comment(self, repo_id: str, pr_id: int, body: str) -> bool:
        """
        Post a general review comment to a pull request.
        """
        pass

    @abstractmethod
    def post_inline_comment(self, repo_id: str, pr_id: int, file: str, line: int, body: str) -> bool:
        """
        Post an inline comment to a specific line in a pull request.
        """
        pass
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
    def get_pull_request_files(self, repo_id: str, pr_id: int) -> list[str]:
        """
        Fetch the list of files changed in a pull request.
        """
        pass

    @abstractmethod
    def get_pull_request_file_diffs(self, repo_id: str, pr_id: int) -> list[dict]:
        """
        Fetch the list of files and their diff patches.
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

    @abstractmethod
    def get_file_content(self, repo_id: str, file_path: str, start_line: int = None, end_line: int = None) -> str:
        """
        Fetch the content of a file.
        If start_line and end_line are provided, returns only that range (1-indexed).
        """
    @abstractmethod
    def get_file_structure(self, repo_id: str, file_path: str) -> str:
        """
        Analyze the file content and return a high-level structure/outline
        (e.g., list of classes and functions with line numbers).
        """
        pass
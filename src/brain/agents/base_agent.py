from src.config import settings

class BaseAgent:
    def __init__(self, llm_client, scm_client):
        self.llm = llm_client
        self.scm = scm_client
        self.tool_call_max_retries = int(settings.tool_call_max_retries)
        self.tool_call_retry_delay = int(settings.tool_call_retry_delay)
        self.registered_tools = {
            "get_file_structure": self.scm.get_file_structure
        }

    def llm_output_validator(self, response_text: str) -> tuple[bool, dict | None, str]:
        raise NotImplementedError("Subclasses must implement this method")

    def run(self, system_prompt: str, user_message: str) -> list:
        raise NotImplementedError("Subclasses must implement this method")
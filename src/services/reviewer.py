import logging
from src.config import settings
from src.services.scm.github import GitHubSCM
from src.services.llm.openai_client import OpenAILLM
from src.services.llm.ollama_client import OllamaLLM
from src.services.llm.anthropic_client import AnthropicLLM
from src.brain.prompts.prompt_registory import get_system_prompt
from src.brain.agents.review_agent import ReviewAgent

# Configure logging
logger = logging.getLogger("reviewer")

class ReviewerService:
    def __init__(self):
        self.scm = GitHubSCM(settings.github_token)
        if settings.llm_provider == "openai":
            self.llm = OpenAILLM()
        elif settings.llm_provider == "ollama":
            self.llm = OllamaLLM()
        elif settings.llm_provider == "anthropic":
            self.llm = AnthropicLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    async def review_pull_request(self, repo_id: str, pr_id: int):
        logger.info(f"Starting review for PR {repo_id}#{pr_id}")
        
        # 1. Fetch Diff
        try:
            diff = self.scm.get_pull_request_diff(repo_id, pr_id)
        except Exception as e:
            logger.error(f"Failed to fetch diff: {e}")
            return

        # 2. Build Prompt
        system_prompt = get_system_prompt()
        user_message = f"Repository: {repo_id}\nPR #{pr_id}\n\nDiff Content:\n{diff}"
        
        # 3. Initialize and Run Agent
        agent = ReviewAgent(self.llm, self.scm)
        try:
            comments = agent.run(system_prompt, user_message)
            return comments
        except Exception as e:
            logger.error(f"Agent failed to complete review: {e}")
            return []


                
                
            

            
            
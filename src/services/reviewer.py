import asyncio
import logging
from src.config import settings
from src.services.scm.github import GitHubSCM
from src.services.llm.openai_client import OpenAILLM
from src.services.llm.ollama_client import OllamaLLM
from src.services.llm.anthropic_client import AnthropicLLM
from src.brain.prompts.prompt_registory import get_system_prompt
from src.brain.agents.review_agent import ReviewAgent
from src.utils.filter_utils import should_review_file
from src.utils.hunk_processor import HunkProcessor
from src.services.semantic_filter import SemanticFilter

logger = logging.getLogger(__name__)

class ReviewerService:
    def __init__(self):
        self.scm = GitHubSCM(settings.github_token)
        self.llm = self._init_llm_client()
        self.semantic_filter = SemanticFilter()

    def _init_llm_client(self):
        """Initialize and return the configured LLM client."""
        providers = {
            "openai": OpenAILLM,
            "ollama": OllamaLLM,
            "anthropic": AnthropicLLM
        }
        
        provider = settings.llm_provider.lower()
        if provider not in providers:
            logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
        return providers[provider]()

    async def review_pull_request(self, repo_id: str, pr_id: int):
        logger.info(f"Starting review for PR {repo_id}#{pr_id}")
        
        try:
            # Fetch PR metadata to get base/head refs for semantic filtering
            pr_data = self.scm.get_pull_request(repo_id, pr_id)
            base_sha = pr_data.get("base", {}).get("sha")
            head_sha = pr_data.get("head", {}).get("sha")
            
            file_diffs = self.scm.get_pull_request_file_diffs(repo_id, pr_id)
        except Exception as e:
            logger.exception(f"Failed to fetch file diffs for PR {pr_id}")
            return []

        review_tasks = []
        for fd in file_diffs:
            filename = fd.get('filename')
            patch = fd.get('patch')
            
            if not patch or not should_review_file(filename):
                continue

            # Semantic Filter: skip files where changes are only comments or whitespace
            try:
                # We offload large file fetching to external threads to keep event loop responsive
                old_content = await asyncio.to_thread(self.scm.get_file_content, repo_id, filename, ref=base_sha)
                new_content = await asyncio.to_thread(self.scm.get_file_content, repo_id, filename, ref=head_sha)
                
                if not self.semantic_filter.is_semantic_change(old_content, new_content, filename):
                    logger.info(f"Skipping {filename}: Change is non-semantic (comments/whitespace only).")
                    continue
            except Exception as e:
                logger.warning(f"Semantic filter failed for {filename}, proceeding with review: {e}")
                
            # Split patch into small focus chunks (e.g. 10 lines of changes)
            chunks = list(HunkProcessor.chunk_patch(filename, patch, settings.review_max_lines))
            review_tasks.extend(chunks)
        
        if not review_tasks:
            logger.info(f"No changes requiring review for PR {pr_id} after filtering.")
            return []

        logger.info(f"Processing {len(review_tasks)} review chunks in {settings.review_execution_mode} mode.")

        system_prompt = get_system_prompt()
        all_comments = []

        if settings.review_execution_mode == "parallel":
            # Concurrent processing with a semaphore to avoid rate limits/overload
            semaphore = asyncio.Semaphore(5)
            
            async def process_task(task):
                async with semaphore:
                    # Offload sync agent call to a thread
                    return await asyncio.to_thread(self._run_agent_on_chunk, system_prompt, repo_id, pr_id, task)
            
            results = await asyncio.gather(*(process_task(t) for t in review_tasks))
            for res in results:
                all_comments.extend(res)
        else:
            for task in review_tasks:
                comments = self._run_agent_on_chunk(system_prompt, repo_id, pr_id, task)
                all_comments.extend(comments)
        
        logger.info(f"Completed PR review with {len(all_comments)} comments.")
        return all_comments

    def _run_agent_on_chunk(self, system_prompt: str, repo_id: str, pr_id: int, chunk: dict) -> list:
        """
        Runs the ReviewAgent on a single code chunk and posts resulting comments.
        """
        filename = chunk['filename']
        start, end = chunk['start_line'], chunk['end_line']
        
        logger.info(f"Reviewing {filename} lines {start}-{end} ({chunk['changes']} changes)")
        
        user_message = (
            f"Repository: {repo_id}\n"
            f"PR #{pr_id}\n"
            f"File: {filename}\n"
            f"Focus Range: Lines {start} - {end}\n\n"
            f"Diff Highlights (Line-numbered):\n"
            f"{chunk['content']}\n\n"
            f"Note: Only provide comments for the lines shown above. Use the provided line numbers exactly."
        )
        
        agent = ReviewAgent(self.llm, self.scm)
        try:
            comments = agent.run(system_prompt, user_message)
            for c in comments:
                # IMPORTANT: Use the filename from the chunk context. 
                # Trusting the agent to return the exact repo-relative path is prone to hallucination 
                # or formatting errors (like adding ./), leading to 'path could not be resolved' API errors.
                self.scm.post_inline_comment(repo_id, pr_id, filename, c['line'], c['comment'])
            return comments
        except Exception as e:
            logger.error(f"Agent failed for {filename} chunk: {e}")
            return []

    async def review_commit(self, repo_id: str, commit_sha: str):
        logger.info(f"Starting review for commit {repo_id}@{commit_sha}")
        
        try:
            diff = self.scm.get_commit_diff(repo_id, commit_sha)
        except Exception as e:
            logger.exception(f"Failed to fetch commit diff: {commit_sha}")
            return []

        system_prompt = get_system_prompt()
        user_message = f"Repository: {repo_id}\nCommit: {commit_sha}\n\nDiff Content:\n{diff}"
        
        agent = ReviewAgent(self.llm, self.scm)
        try:
            comments = agent.run(system_prompt, user_message)
            for c in comments:
                self.scm.post_commit_inline_comment(repo_id, commit_sha, c['file'], c['line'], c['comment'])
            logger.info(f"Completed commit review with {len(comments)} comments.")
            return comments
        except Exception as e:
            logger.error(f"Agent failed to complete commit review: {e}")
            return []

if __name__ == "__main__":
    # Test execution
    import sys
    async def main():
        reviewer = ReviewerService()
        await reviewer.review_pull_request("Lmalviya/Pull-Request-Pilot", 1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

    
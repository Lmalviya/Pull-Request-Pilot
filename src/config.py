import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class Settings(BaseSettings):
    github_token: str = os.getenv("GITHUB_TOKEN")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME")
    openai_model: str = os.getenv("OPENAI_MODEL")
    app_name: str = "Pull Request Pilot"
    debug: bool = False
    github_base_url: str = os.getenv("GITHUB_BASE_URL")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL")
    llm_provider: str = os.getenv("LLM_PROVIDER")
    
    ollama_model: str = os.getenv("OLLAMA_MODEL")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL")
    anthropic_base_url: str = os.getenv("ANTHROPIC_BASE_URL")
    system_prompt_name: str = os.getenv("SYSTEM_PROMPT_NAME")
    tool_call_max_retries: int = os.getenv("TOOL_CALL_MAX_RETRIES", 3)
    tool_call_retry_delay: int = os.getenv("TOOL_CALL_RETRY_DELAY", 5)
    
    # Review Strategy
    review_max_lines: int = int(os.getenv("REVIEW_MAX_LINES", 10))
    review_execution_mode: str = os.getenv("REVIEW_EXECUTION_MODE", "sequential")
    ignored_extensions: str = os.getenv("IGNORED_EXTENSIONS", ".lock,.json,.map,.svg,.png,.jpg,.jpeg,.pyc,.yml,.toml,.pyd,.md")
    ignored_files: str = os.getenv("IGNORED_FILES", ".gitignore,.env,LICENSE,CONTRIBUTING.md")
    ignored_directories: str = os.getenv("IGNORED_DIRECTORIES", "__pycache__,node_modules,.venv,tests,migrations")
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def __init__(self):
        super().__init__()
        
        # Ensure required env vars are set
        required_vars = ["github_token", "github_webhook_secret", "system_prompt_name"]
        missing_vars = [v for v in required_vars if not getattr(self, v, None)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join([v.upper() for v in missing_vars])}")
        
        # Validate llm_provider
        allowed_providers = [provider.value for provider in LLMProvider]
        if not self.llm_provider:
            raise ValueError("LLM_PROVIDER must be set in environment variables")
        if self.llm_provider.lower() not in allowed_providers:
            raise ValueError(f"LLM_PROVIDER must be one of: {', '.join(allowed_providers)}. Got: {self.llm_provider}")

settings = Settings()

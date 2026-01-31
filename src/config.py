import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # GitHub settings
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # LLM settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20240620")

    # API settings
    APP_NAME: str = "Pull Request Pilot"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()

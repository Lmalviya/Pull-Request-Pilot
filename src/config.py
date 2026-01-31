from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    github_webhook_secret: str
    github_token: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    model_name: str = "claude-3-5-sonnet-20240620"
    openai_model: str = "gpt-4-turbo"
    app_name: str = "Pull Request Pilot"
    debug: bool = False
    github_base_url: str = "https://api.github.com"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    openai_base_url: str = "https://api.openai.com/v1/chat/completions"
    anthropic_base_url: str = "https://api.anthropic.com/v1/messages"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

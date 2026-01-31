from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    github_webhook_secret: str
    github_token: str = ""
    anthropic_api_key: str = ""
    model_name: str = "claude-3-5-sonnet-20240620"
    app_name: str = "Pull Request Pilot"
    debug: bool = False
    github_base_url: str = "https://api.github.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

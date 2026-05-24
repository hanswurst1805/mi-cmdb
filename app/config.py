from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://cmdb:cmdb@localhost:5432/cmdb"
    openrouter_api_key: str = ""
    openrouter_chat_model: str = "anthropic/claude-sonnet-4-6"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    admin_username: str = "admin"
    admin_password: str = "changeme"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()

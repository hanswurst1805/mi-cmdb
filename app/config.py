from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://cmdb:cmdb@localhost:5432/cmdb"
    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()

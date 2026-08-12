import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://travel:travel@localhost:5432/travel_planner"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me-to-a-long-random-value"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"), extra="ignore")


settings = Settings()

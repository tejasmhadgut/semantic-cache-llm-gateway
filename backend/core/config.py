from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn


class Settings(BaseSettings):
    database_url: PostgresDsn
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    REDIS_URL: str
    RABBITMQ_URL: str
    RATE_LIMIT_REQUESTS: int
    RATE_LIMIT_WINDOW: int
    CACHE_TTL_SECONDS: int
    class Config:
        env_file = ".env"

settings = Settings()
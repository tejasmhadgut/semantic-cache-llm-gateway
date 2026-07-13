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
    SENTINEL_HOSTS: str = "sentinel-1:26379,sentinel-2:26379,sentinel-3:26379"
    REDIS_MASTER_NAME: str = "mymaster"

    class Config:
        env_file = ".env"

settings = Settings()
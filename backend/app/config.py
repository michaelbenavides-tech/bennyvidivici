from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "aisgp"
    postgres_user: str = "aisgp"
    postgres_password: str = "changeme_in_production"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = "changeme_in_production"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "changeme_in_production"
    minio_bucket_artifacts: str = "ai-sgp-artifacts"
    minio_bucket_evidence: str = "ai-sgp-evidence"
    minio_use_ssl: bool = False
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "ai-sgp"
    keycloak_client_id: str = "ai-sgp-backend"
    secret_key: str = Field("dev-only", min_length=6)
    cors_origins: list[str] = ["http://localhost", "http://localhost:5173"]
    environment: str = "development"
    auth_disabled: bool = True

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

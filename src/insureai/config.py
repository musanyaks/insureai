"""Central configuration. Everything reads from here; nothing reads os.environ directly."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "insureai"
    postgres_password: str = "insureai"
    postgres_db: str = "insureai"

    kafka_bootstrap: str = "localhost:9092"

    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    environment: str = "dev"

    inline_agents: bool = False    # run agent fleet inside the API process (memory bus demos)

    jwt_secret: str = "dev-secret-change-me"
    bus_backend: str = "memory"            # memory | kafka
    cors_origins: str = "http://localhost:3000"

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# ------------  Environment Types ------------


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PROD = "prod"


# ------------  Sub-config Models ------------


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: SecretStr
    database: str = "app"

    @property
    def url(self) -> str:
        return (
            f"postgresql://"
            f"{self.username}:"
            f"{self.password.get_secret_value()}@"
            f"{self.host}:"
            f"{self.port}/"
            f"{self.database}"
        )


class LoggingSettings(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_logs: bool = False


class AwsSettings(BaseModel):
    region: str = "eu-west-2"
    bucket_name: str = "my-app-dev"


# ------------ Main Settings ------------


class Settings(BaseSettings):
    """
    Main application settings.

    Environment variables use:
        APP_

    Nested settings use:
        __

    Example:
        APP_DB__HOST=localhost
        APP_DB__PASSWORD=secret
    """

    # -----------------------------------------------------
    # Pydantic Settings Config
    # -----------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------ Core App Settings ------------

    app_name: str = "my-app"
    environment: Environment = Environment.DEV
    debug: bool = False

    # Paths

    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path("/tmp/my-app-data")

    # ------------ Feature Flags ------------

    enable_metrics: bool = True
    enable_tracing: bool = False

    # ------------ Nested Config Sections ------------

    db: DatabaseSettings
    logging: LoggingSettings = LoggingSettings()
    aws: AwsSettings = AwsSettings()

    # Computed Properties

    @property
    def is_dev(self) -> bool:
        return self.environment == Environment.DEV

    @property
    def is_test(self) -> bool:
        return self.environment == Environment.TEST

    @property
    def is_staging(self) -> bool:
        return self.environment == Environment.STAGING

    @property
    def is_prod(self) -> bool:
        return self.environment == Environment.PROD

    @property
    def running_in_cloud(self) -> bool:
        """
        Example heuristic.

        Adjust based on your platform:
        - KUBERNETES_SERVICE_HOST
        - ECS_CONTAINER_METADATA_URI
        - etc.
        """
        import os

        return (
            "KUBERNETES_SERVICE_HOST" in os.environ
            or "ECS_CONTAINER_METADATA_URI" in os.environ
        )


# ------------  Cached Settings Instance ------------


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings singleton.

    Prevents:
    - repeated env parsing
    - repeated .env reads
    - duplicate object creation
    """

    settings = Settings()

    # Ensure runtime dirs exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    return settings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    param1: str
    param2: str
    env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env")


def get_settings():
    return Settings()

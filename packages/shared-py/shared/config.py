from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Elio"
    environment: str = Field(default="development")
    database_url: str = Field(
        default="postgresql+psycopg://elio:elio@localhost:5432/elio"
    )
    broker_url: str = Field(default="localhost:9092")
    jwt_secret: str = Field(default="change-me")
    llm_model: str = Field(default="gpt-5-mini")


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "MaaV Solutions Phase-1"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = "YOUR_SECRET_KEY"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database: Single URL source of truth
    # Must be in format: postgresql+asyncpg://...
    DATABASE_URL: PostgresDsn

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        url = str(self.DATABASE_URL)
        
        # Strict validation: Explicitly require asyncpg driver
        if "asyncpg" not in url:
            raise ValueError(
                "DATABASE_URL must be an async connection string. "
                "Format: postgresql+asyncpg://user:password@host:port/db"
            )
             
        return url

settings = Settings()

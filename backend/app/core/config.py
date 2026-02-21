from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field, model_validator
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "MaaV Solutions Phase-1"
    API_V1_STR: str = "/api/v1"
    
    JWT_SECRET_KEY: str = "YOUR_SUPER_SECRET_JWT_KEY_HERE"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

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

    @model_validator(mode='after')
    def validate_production_secrets(self):
        if self.APP_ENV.lower() == "production":
            if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "YOUR_SUPER_SECRET_JWT_KEY_HERE":
                raise RuntimeError("JWT_SECRET_KEY must be set securely in production")
        return self

settings = Settings()

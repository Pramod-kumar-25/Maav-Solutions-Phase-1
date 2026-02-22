from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field, model_validator, SecretStr
from typing import Optional, Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "MaaV Solutions Phase-1"
    API_V1_STR: str = "/api/v1"
    
    # Secrets classification: SecretStr protects against accidental logging exposure.
    # NO DEFAULT VALUE: Fails securely on startup if missing.
    JWT_SECRET_KEY: SecretStr
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Environment MUST be explicitly declared. No silent fallbacks to development.
    APP_ENV: Literal["development", "staging", "production"]
    LOG_LEVEL: str = "INFO"

    # CORS Settings
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

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
        env = self.APP_ENV.lower()
        
        if env in ["staging", "production"]:
            if self.LOG_LEVEL.upper() == "DEBUG":
                 raise ValueError(f"LOG_LEVEL 'DEBUG' is strictly prohibited in {env} environment.")
        
        if env == "production":
            jwt_secret = self.JWT_SECRET_KEY.get_secret_value()
            if not jwt_secret or jwt_secret == "YOUR_SUPER_SECRET_JWT_KEY_HERE":
                raise ValueError("JWT_SECRET_KEY must be generated uniquely for production.")
            
            # 256-bit Entropy Enforcement
            if len(jwt_secret.encode('utf-8')) < 32:
                 raise ValueError(
                     "JWT_SECRET_KEY lacks sufficient entropy. "
                     "Must be at least 32 bytes (cryptographically generated) to satisfy HS256."
                 )
                 
            # CORS Fail-Closed Security Validation
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError("BACKEND_CORS_ORIGINS cannot be empty in production.")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Wildcard '*' origins are strictly prohibited in production.")
                
        return self

settings = Settings()

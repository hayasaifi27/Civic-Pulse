from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import json


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    debug: bool = Field(default=True, alias="DEBUG")

    database_url: str = Field(alias="DATABASE_URL")
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_anon_key: str = Field(alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_storage_bucket: str = Field(default="civicpulse-media", alias="SUPABASE_STORAGE_BUCKET")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    vision_provider: str = Field(default="mock", alias="VISION_PROVIDER")
    vision_api_key: str = Field(default="", alias="VISION_API_KEY")
    vision_model: str = Field(default="gpt-4-vision-preview", alias="VISION_MODEL")

    agent_mode: str = Field(default="development", alias="AGENT_MODE")
    agent_seed: str = Field(alias="AGENT_SEED")
    agent_endpoint: str = Field(default="http://localhost:8000/agent/webhook", alias="AGENT_ENDPOINT")
    classification_agent_address: str = Field(default="", alias="CLASSIFICATION_AGENT_ADDRESS")
    duplicate_agent_address: str = Field(default="", alias="DUPLICATE_AGENT_ADDRESS")
    priority_agent_address: str = Field(default="", alias="PRIORITY_AGENT_ADDRESS")

    cors_allowed_origins_raw: str = Field(
        default='["http://localhost:5173","http://localhost:3000"]',
        alias="CORS_ALLOWED_ORIGINS"
    )

    email_provider: str = Field(default="mock", alias="EMAIL_PROVIDER")
    email_api_key: str = Field(default="", alias="EMAIL_API_KEY")
    email_from: str = Field(default="noreply@civicpulse.local", alias="EMAIL_FROM")

    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")

    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    max_file_size: int = Field(default=10485760, alias="MAX_FILE_SIZE")
    allowed_file_types_raw: str = Field(
        default='["image/jpeg","image/png","image/webp","image/heic"]',
        alias="ALLOWED_FILE_TYPES"
    )

    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, alias="JWT_EXPIRY_HOURS")
    refresh_token_expiry_days: int = Field(default=30, alias="REFRESH_TOKEN_EXPIRY_DAYS")

    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")

    @property
    def cors_allowed_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_allowed_origins_raw)
        except Exception:
            return ["http://localhost:5173", "http://localhost:3000"]

    @property
    def allowed_file_types(self) -> List[str]:
        try:
            return json.loads(self.allowed_file_types_raw)
        except Exception:
            return ["image/jpeg", "image/png", "image/webp", "image/heic"]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
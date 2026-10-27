from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    environment: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-change-me"
    site_url: str = "http://localhost:3000"
    allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    admin_url_path: str = "admin"
    app_version: str = "dev"
    git_commit: str = "unknown"

    database_url: str = "postgresql+asyncpg://dortech:dortech@localhost:5432/dortech"
    test_database_url: str = "postgresql+asyncpg://dortech:dortech@localhost:5432/dortech_test"

    media_root: Path = BASE_DIR / "media"
    private_root: Path = BASE_DIR / "private"
    logs_root: Path = BASE_DIR / "logs"
    max_upload_mb: int = 20
    allowed_upload_extensions: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"]
    )

    session_cookie_name: str = "dt_session"
    session_ttl_days: int = 14
    csrf_cookie_name: str = "dt_csrf"
    email_token_ttl_hours: int = 24

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    default_from_email: str = "Дортех <noreply@localhost>"
    notification_emails: Annotated[list[str], NoDecode] = Field(default_factory=list)

    webhook_url: str = ""
    webhook_secret: str = ""
    webhook_sink_enabled: bool = False

    rate_limit_enabled: bool = True
    robots_allow: bool = True
    sentry_dsn: str = ""
    log_level: str = "INFO"

    @field_validator("allowed_hosts", "notification_emails", "allowed_upload_extensions", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

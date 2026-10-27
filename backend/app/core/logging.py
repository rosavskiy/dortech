import logging
import logging.config

from app.core.config import settings


def setup_logging() -> None:
    settings.logs_root.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "std": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "std"},
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "std",
                    "filename": str(settings.logs_root / "app-error.log"),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "level": "WARNING",
                    "encoding": "utf-8",
                },
            },
            "root": {"level": settings.log_level, "handlers": ["console", "error_file"]},
            "loggers": {
                "uvicorn.access": {"level": "INFO", "propagate": True},
                "sqlalchemy.engine": {"level": "WARNING"},
            },
        }
    )

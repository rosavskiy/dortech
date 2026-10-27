import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ImportStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, native_enum=False, length=20), default=ImportStatus.pending, nullable=False
    )
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    skipped: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    errors: Mapped[list | None] = mapped_column(JSONB)
    report_file: Mapped[str | None] = mapped_column(String(500))
    started_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    started_by: Mapped["User | None"] = relationship()  # noqa: F821

    def __str__(self) -> str:
        return f"Импорт #{self.id} {self.file_name}"


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    events: Mapped[list | None] = mapped_column(JSONB, default=lambda: ["inquiry.created"])
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __str__(self) -> str:
        return self.name


class OutboundKind(str, enum.Enum):
    email = "email"
    webhook = "webhook"


class OutboundStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class OutboundMessage(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[OutboundKind] = mapped_column(Enum(OutboundKind, native_enum=False, length=20), nullable=False)
    endpoint_id: Mapped[int | None] = mapped_column(ForeignKey("webhook_endpoints.id", ondelete="SET NULL"))
    event: Mapped[str | None] = mapped_column(String(50))
    delivery_id: Mapped[str | None] = mapped_column(String(36), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[OutboundStatus] = mapped_column(
        Enum(OutboundStatus, native_enum=False, length=20), default=OutboundStatus.pending, nullable=False, index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_error: Mapped[str | None] = mapped_column(Text)
    response_code: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    endpoint: Mapped[WebhookEndpoint | None] = relationship()

    def __str__(self) -> str:
        return f"{self.kind.value} #{self.id} ({self.status.value})"


class WebhookDelivery(Base):
    """Тестовый приёмник webhook (включается WEBHOOK_SINK_ENABLED=1)."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    headers: Mapped[dict | None] = mapped_column(JSONB)
    body: Mapped[dict | None] = mapped_column(JSONB)
    signature_valid: Mapped[bool | None] = mapped_column(Boolean)

    def __str__(self) -> str:
        return f"Доставка #{self.id}"

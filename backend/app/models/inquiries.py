import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class InquiryStatus(str, enum.Enum):
    new = "new"
    clarification = "clarification"
    offer_sent = "offer_sent"
    agreed = "agreed"
    completed = "completed"
    cancelled = "cancelled"


STATUS_LABELS = {
    InquiryStatus.new: "Новая",
    InquiryStatus.clarification: "Уточнение",
    InquiryStatus.offer_sent: "Предложение направлено",
    InquiryStatus.agreed: "Согласована",
    InquiryStatus.completed: "Завершена",
    InquiryStatus.cancelled: "Отменена",
}

# Допустимые переходы (ТЗ 3.3). Администратор может выполнять любой переход.
STATUS_TRANSITIONS: dict[InquiryStatus, set[InquiryStatus]] = {
    InquiryStatus.new: {InquiryStatus.clarification, InquiryStatus.offer_sent, InquiryStatus.cancelled},
    InquiryStatus.clarification: {InquiryStatus.offer_sent, InquiryStatus.cancelled},
    InquiryStatus.offer_sent: {InquiryStatus.clarification, InquiryStatus.agreed, InquiryStatus.cancelled},
    InquiryStatus.agreed: {InquiryStatus.completed, InquiryStatus.cancelled},
    InquiryStatus.completed: set(),
    InquiryStatus.cancelled: {InquiryStatus.new},
}


class InquirySource(str, enum.Enum):
    web = "web"
    account = "account"
    repeat = "repeat"


class RateUnit(str, enum.Enum):
    shift = "shift"
    day = "day"


class Inquiry(TimestampMixin, Base):
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, default=new_uuid, nullable=False)
    number: Mapped[str | None] = mapped_column(String(20), unique=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    company_name_raw: Mapped[str | None] = mapped_column(String(255))
    period_from: Mapped[date | None] = mapped_column(Date)
    period_to: Mapped[date | None] = mapped_column(Date)
    work_place: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[InquiryStatus] = mapped_column(
        Enum(InquiryStatus, native_enum=False, length=20), default=InquiryStatus.new, nullable=False, index=True
    )
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    estimated_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    estimate_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[InquirySource] = mapped_column(
        Enum(InquirySource, native_enum=False, length=20), default=InquirySource.web, nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("inquiries.id", ondelete="SET NULL"))
    ip: Mapped[str | None] = mapped_column(String(64))

    organization: Mapped["Organization | None"] = relationship()  # noqa: F821
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(foreign_keys=[assigned_to_id])  # noqa: F821
    parent: Mapped["Inquiry | None"] = relationship(remote_side=[id])
    items: Mapped[list["InquiryItem"]] = relationship(back_populates="inquiry", cascade="all, delete-orphan")
    extra_services: Mapped[list["InquiryExtraService"]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["InquiryStatusHistory"]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan", order_by="InquiryStatusHistory.created_at"
    )
    comments: Mapped[list["InquiryComment"]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan", order_by="InquiryComment.created_at"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="inquiry", cascade="all, delete-orphan", order_by="Attachment.created_at"
    )

    def __str__(self) -> str:
        return self.number or f"Заявка #{self.id}"


class InquiryItem(Base):
    __tablename__ = "inquiry_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    model_snapshot: Mapped[str | None] = mapped_column(String(150))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    units: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit: Mapped[RateUnit] = mapped_column(
        Enum(RateUnit, native_enum=False, length=10), default=RateUnit.shift, nullable=False
    )
    unit_price_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    needs_quote: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    inquiry: Mapped[Inquiry] = relationship(back_populates="items")
    equipment: Mapped["Equipment"] = relationship()  # noqa: F821

    def __str__(self) -> str:
        return f"{self.name_snapshot} × {self.quantity}"


class InquiryExtraService(Base):
    __tablename__ = "inquiry_extra_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("extra_services.id", ondelete="SET NULL"))
    name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    inquiry: Mapped[Inquiry] = relationship(back_populates="extra_services")

    def __str__(self) -> str:
        return self.name_snapshot


class InquiryStatusHistory(Base):
    __tablename__ = "inquiry_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    from_status: Mapped[InquiryStatus | None] = mapped_column(Enum(InquiryStatus, native_enum=False, length=20))
    to_status: Mapped[InquiryStatus] = mapped_column(Enum(InquiryStatus, native_enum=False, length=20), nullable=False)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inquiry: Mapped[Inquiry] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship()  # noqa: F821


class InquiryComment(Base):
    __tablename__ = "inquiry_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inquiry: Mapped[Inquiry] = relationship(back_populates="comments")
    author: Mapped["User | None"] = relationship()  # noqa: F821


class AttachmentKind(str, enum.Enum):
    client_doc = "client_doc"
    offer_pdf = "offer_pdf"


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[uuid.UUID] = mapped_column(unique=True, index=True, default=new_uuid, nullable=False)
    inquiry_id: Mapped[int] = mapped_column(ForeignKey("inquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), index=True)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[AttachmentKind] = mapped_column(
        Enum(AttachmentKind, native_enum=False, length=20), default=AttachmentKind.client_doc, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inquiry: Mapped[Inquiry] = relationship(back_populates="attachments")
    uploaded_by: Mapped["User | None"] = relationship()  # noqa: F821

    def __str__(self) -> str:
        return self.original_name


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64))
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __str__(self) -> str:
        return f"{self.name} ({self.created_at:%d.%m.%Y})" if self.created_at else self.name

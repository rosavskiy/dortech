from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.inquiries import InquiryStatus, RateUnit


class ProfileIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    patronymic: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=32)
    position: str | None = Field(default=None, max_length=150)
    org_name: str = Field(min_length=2, max_length=255)
    org_inn: str | None = Field(default=None, max_length=12)
    org_kpp: str | None = Field(default=None, max_length=9)
    org_legal_address: str | None = Field(default=None, max_length=1000)
    org_phone: str | None = Field(default=None, max_length=32)
    org_email: str | None = Field(default=None, max_length=255)


class UserBrief(BaseModel):
    id: int
    name: str
    email: str | None = None
    role: str


class ItemOut(BaseModel):
    equipment_id: int
    slug: str | None = None
    name: str
    model: str | None = None
    quantity: int
    units: int
    unit: RateUnit
    unit_price: Decimal | None = None
    line_total: Decimal | None = None
    needs_quote: bool


class ExtraOut(BaseModel):
    name: str
    price: Decimal


class HistoryOut(BaseModel):
    from_status: InquiryStatus | None
    to_status: InquiryStatus
    to_label: str
    changed_by: str | None = None
    comment: str | None = None
    created_at: datetime


class CommentOut(BaseModel):
    id: int
    author: str
    is_staff: bool
    is_internal: bool
    text: str
    created_at: datetime


class AttachmentOut(BaseModel):
    public_id: UUID
    original_name: str
    content_type: str
    size: int
    kind: str
    uploaded_by: str | None = None
    created_at: datetime
    download_url: str


class InquiryBrief(BaseModel):
    public_id: UUID
    number: str
    status: InquiryStatus
    status_label: str
    created_at: datetime
    period_from: date | None
    period_to: date | None
    items_count: int
    estimated_total: Decimal | None
    is_partial: bool
    organization: str | None = None
    contact_name: str
    assigned_to: UserBrief | None = None
    source: str


class InquiryDetail(InquiryBrief):
    contact_phone: str
    contact_email: str | None
    work_place: str | None
    comment: str | None
    items: list[ItemOut]
    extras: list[ExtraOut]
    total_label: str
    vat_label: str | None = None
    history: list[HistoryOut]
    comments: list[CommentOut]
    attachments: list[AttachmentOut]
    allowed_transitions: list[InquiryStatus] = []
    parent_number: str | None = None


class CommentIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    is_internal: bool = False


class StatusIn(BaseModel):
    status: InquiryStatus
    comment: str | None = Field(default=None, max_length=2000)


class AssignIn(BaseModel):
    assigned_to_id: int | None = None

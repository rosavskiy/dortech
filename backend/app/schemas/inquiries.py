from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.inquiries import InquiryStatus, RateUnit


class EstimateItemIn(BaseModel):
    equipment_id: int
    quantity: int = Field(default=1, ge=1, le=100)
    units: int | None = Field(default=None, ge=1, le=366)
    unit: RateUnit = RateUnit.shift


class EstimateIn(BaseModel):
    items: list[EstimateItemIn] = Field(min_length=1, max_length=10)
    period_from: date | None = None
    period_to: date | None = None
    extra_service_ids: list[int] = []


class EstimateLine(BaseModel):
    equipment_id: int
    name: str
    model: str | None = None
    quantity: int
    units: int
    unit: RateUnit
    unit_price: Decimal | None = None
    line_total: Decimal | None = None
    needs_quote: bool = False


class EstimateExtra(BaseModel):
    id: int
    name: str
    price: Decimal


class EstimateOut(BaseModel):
    lines: list[EstimateLine]
    extras: list[EstimateExtra]
    total: Decimal
    is_partial: bool
    currency: str = "RUB"
    vat_label: str
    disclaimer: str
    rounding_step: int


class InquiryCreateIn(EstimateIn):
    contact_name: str = Field(min_length=2, max_length=200)
    contact_phone: str = Field(min_length=6, max_length=32)
    contact_email: EmailStr | None = None
    company_name: str | None = Field(default=None, max_length=255)
    work_place: str | None = Field(default=None, max_length=2000)
    comment: str | None = Field(default=None, max_length=4000)
    consent: bool
    website: str | None = None  # honeypot
    parent_public_id: UUID | None = None

    @field_validator("consent")
    @classmethod
    def _consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Необходимо согласие на обработку персональных данных")
        return v


class InquiryCreatedOut(BaseModel):
    public_id: UUID
    number: str
    status: InquiryStatus
    estimate: EstimateOut
    created_at: datetime


class ContactMessageIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    email: EmailStr | None = None
    text: str = Field(min_length=5, max_length=4000)
    consent: bool
    website: str | None = None

    @field_validator("consent")
    @classmethod
    def _consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Необходимо согласие на обработку персональных данных")
        return v

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    parent_id: int | None = None
    description: str | None = None
    image_url: str | None = None
    is_featured: bool = False
    equipment_count: int = 0


class ManufacturerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    logo_url: str | None = None


class StatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    color: str
    allow_request: bool


class TariffOut(BaseModel):
    price_per_shift: Decimal | None = None
    price_per_day: Decimal | None = None
    shift_hours: int = 8
    min_units: int = 1
    note: str | None = None


class AttributeValueOut(BaseModel):
    code: str
    name: str
    unit: str | None = None
    value: str
    raw: str | float | bool | None = None


class ImageOut(BaseModel):
    url: str
    alt: str | None = None


class EquipmentCard(BaseModel):
    id: int
    slug: str
    name: str
    model: str | None = None
    year: int | None = None
    category: CategoryOut
    manufacturer: ManufacturerOut | None = None
    status: StatusOut | None = None
    image: ImageOut | None = None
    short_description: str | None = None
    price_hidden: bool = False
    tariff: TariffOut | None = None
    is_featured: bool = False
    key_attributes: list[AttributeValueOut] = []


class EquipmentDetail(EquipmentCard):
    description: str | None = None
    terms: str | None = None
    images: list[ImageOut] = []
    attributes: list[AttributeValueOut] = []
    meta_title: str | None = None
    meta_description: str | None = None
    og_image_url: str | None = None
    noindex: bool = False


class FacetOption(BaseModel):
    value: str
    label: str
    count: int


class FacetAttribute(BaseModel):
    code: str
    name: str
    unit: str | None = None
    type: str
    options: list[FacetOption] = []
    min: Decimal | None = None
    max: Decimal | None = None


class Facets(BaseModel):
    manufacturers: list[FacetOption]
    statuses: list[FacetOption]
    categories: list[FacetOption]
    attributes: list[FacetAttribute]


class CompareRow(BaseModel):
    code: str
    name: str
    unit: str | None = None
    values: list[str | None]


class CompareOut(BaseModel):
    items: list[EquipmentCard]
    rows: list[CompareRow]

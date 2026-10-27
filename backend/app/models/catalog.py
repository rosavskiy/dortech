import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SeoMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.pricing import Tariff


class Category(SeoMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image: Mapped[dict | None] = mapped_column(JSONB)
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    parent: Mapped["Category | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    attributes: Mapped[list["AttributeDefinition"]] = relationship(
        secondary="category_attributes", back_populates="categories"
    )

    def __str__(self) -> str:
        return self.name


class Manufacturer(TimestampMixin, Base):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    logo: Mapped[dict | None] = mapped_column(JSONB)
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    def __str__(self) -> str:
        return self.name


class AvailabilityStatus(Base):
    __tablename__ = "availability_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="gray", server_default="gray")
    allow_request: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    def __str__(self) -> str:
        return self.name


class AttributeType(str, enum.Enum):
    number = "number"
    string = "string"
    bool = "bool"
    choice = "choice"


category_attributes = Table(
    "category_attributes",
    Base.metadata,
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_id", ForeignKey("attribute_definitions.id", ondelete="CASCADE"), primary_key=True),
)


class AttributeDefinition(Base):
    __tablename__ = "attribute_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(30))
    type: Mapped[AttributeType] = mapped_column(
        Enum(AttributeType, native_enum=False, length=20), nullable=False, default=AttributeType.string
    )
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_comparable: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    categories: Mapped[list[Category]] = relationship(secondary=category_attributes, back_populates="attributes")
    options: Mapped[list["AttributeOption"]] = relationship(
        back_populates="attribute", cascade="all, delete-orphan", order_by="AttributeOption.sort"
    )

    def __str__(self) -> str:
        return self.name


class AttributeOption(Base):
    __tablename__ = "attribute_options"
    __table_args__ = (UniqueConstraint("attribute_id", "value", name="uq_attribute_option"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attribute_definitions.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(150), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    attribute: Mapped[AttributeDefinition] = relationship(back_populates="options")

    def __str__(self) -> str:
        return self.value


class Equipment(SeoMixin, TimestampMixin, Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    manufacturer_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id", ondelete="SET NULL"), index=True)
    model: Mapped[str | None] = mapped_column(String(150))
    year: Mapped[int | None] = mapped_column(Integer)
    short_description: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    status_id: Mapped[int | None] = mapped_column(
        ForeignKey("availability_statuses.id", ondelete="SET NULL"), index=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    price_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    category: Mapped[Category] = relationship()
    manufacturer: Mapped[Manufacturer | None] = relationship()
    status: Mapped[AvailabilityStatus | None] = relationship()
    images: Mapped[list["EquipmentImage"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan", order_by="EquipmentImage.sort"
    )
    attribute_values: Mapped[list["AttributeValue"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )
    tariff: Mapped["Tariff | None"] = relationship(
        back_populates="equipment", cascade="all, delete-orphan", uselist=False
    )

    def __str__(self) -> str:
        return f"{self.name} {self.model or ''}".strip()


class EquipmentImage(Base):
    __tablename__ = "equipment_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file: Mapped[dict] = mapped_column(JSONB, nullable=False)
    alt: Mapped[str | None] = mapped_column(String(255))
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    equipment: Mapped[Equipment] = relationship(back_populates="images")

    def __str__(self) -> str:
        return (self.file or {}).get("filename", "") if isinstance(self.file, dict) else str(self.file)


class AttributeValue(Base):
    __tablename__ = "attribute_values"
    __table_args__ = (UniqueConstraint("equipment_id", "attribute_id", name="uq_attribute_value"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attribute_definitions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), index=True)
    value_text: Mapped[str | None] = mapped_column(String(255))
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    option_id: Mapped[int | None] = mapped_column(ForeignKey("attribute_options.id", ondelete="SET NULL"), index=True)

    equipment: Mapped[Equipment] = relationship(back_populates="attribute_values")
    attribute: Mapped[AttributeDefinition] = relationship()
    option: Mapped[AttributeOption | None] = relationship()

    @property
    def display(self) -> str:
        if self.option is not None:
            return self.option.value
        if self.value_bool is not None:
            return "Да" if self.value_bool else "Нет"
        if self.value_number is not None:
            n = self.value_number.normalize()
            return f"{n:f}" if n != n.to_integral() else str(int(n))
        return self.value_text or ""

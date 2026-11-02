from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Tariff(TimestampMixin, Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    price_per_shift: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    price_per_day: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    shift_hours: Mapped[int] = mapped_column(Integer, default=8, server_default="8")
    min_units: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    note: Mapped[str | None] = mapped_column(Text)

    equipment: Mapped["Equipment"] = relationship(back_populates="tariff")  # noqa: F821

    def __str__(self) -> str:
        return f"Тариф #{self.id}"


class ExtraService(TimestampMixin, Base):
    __tablename__ = "extra_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    def __str__(self) -> str:
        return self.name


class PricingSettings(Base):
    __tablename__ = "pricing_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    rounding_step: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    vat_label: Mapped[str] = mapped_column(String(100), default="без НДС", server_default="без НДС")
    disclaimer_text: Mapped[str] = mapped_column(
        Text,
        default="Расчёт предварительный и не является офертой. Окончательные условия подтверждает менеджер.",
        server_default="Расчёт предварительный и не является офертой. Окончательные условия подтверждает менеджер.",
    )

    def __str__(self) -> str:
        return "Настройки расчёта"

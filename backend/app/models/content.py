from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SeoMixin, TimestampMixin


class Page(SeoMixin, TimestampMixin, Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    show_in_footer: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    def __str__(self) -> str:
        return self.title


class Service(SeoMixin, TimestampMixin, Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    cover: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(100))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    def __str__(self) -> str:
        return self.title


class Project(SeoMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    cover: Mapped[str | None] = mapped_column(String(500))
    year: Mapped[int | None] = mapped_column(Integer)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    images: Mapped[list["ProjectImage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProjectImage.sort"
    )

    def __str__(self) -> str:
        return self.title


class ProjectImage(Base):
    __tablename__ = "project_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file: Mapped[str] = mapped_column(String(500), nullable=False)
    alt: Mapped[str | None] = mapped_column(String(255))
    sort: Mapped[int] = mapped_column(Integer, default=100, server_default="100")

    project: Mapped[Project] = relationship(back_populates="images")

    def __str__(self) -> str:
        return self.file


class Publication(SeoMixin, TimestampMixin, Base):
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    cover: Mapped[str | None] = mapped_column(String(500))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __str__(self) -> str:
        return self.title


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), default="ООО «ДОРТЕХ»", server_default="ООО «ДОРТЕХ»")
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    working_hours: Mapped[str | None] = mapped_column(String(255))
    map_embed: Mapped[str | None] = mapped_column(Text)
    hero_title: Mapped[str | None] = mapped_column(String(255))
    hero_subtitle: Mapped[str | None] = mapped_column(Text)
    hero_image: Mapped[str | None] = mapped_column(String(500))
    about_short: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict | None] = mapped_column(JSONB)
    footer_text: Mapped[str | None] = mapped_column(Text)
    default_meta_title: Mapped[str | None] = mapped_column(String(255))
    default_meta_description: Mapped[str | None] = mapped_column(Text)

    def __str__(self) -> str:
        return "Настройки сайта"


class Redirect(TimestampMixin, Base):
    __tablename__ = "redirects"

    id: Mapped[int] = mapped_column(primary_key=True)
    old_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    new_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, default=301, server_default="301")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __str__(self) -> str:
        return f"{self.old_path} → {self.new_path}"

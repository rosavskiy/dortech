from datetime import datetime

from pydantic import BaseModel


class SeoOut(BaseModel):
    meta_title: str | None = None
    meta_description: str | None = None
    og_image_url: str | None = None
    noindex: bool = False


class SiteSettingsOut(BaseModel):
    company_name: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    working_hours: str | None = None
    map_embed: str | None = None
    hero_title: str | None = None
    hero_subtitle: str | None = None
    hero_image_url: str | None = None
    about_short: str | None = None
    stats: list | dict | None = None
    footer_text: str | None = None
    default_meta_title: str | None = None
    default_meta_description: str | None = None
    footer_pages: list["PageBrief"] = []


class PageBrief(BaseModel):
    slug: str
    title: str


class PageOut(SeoOut):
    slug: str
    title: str
    body: str | None = None
    updated_at: datetime


class ServiceOut(SeoOut):
    id: int
    slug: str
    title: str
    short_description: str | None = None
    body: str | None = None
    cover_url: str | None = None
    icon: str | None = None
    updated_at: datetime


class ProjectOut(SeoOut):
    id: int
    slug: str
    title: str
    short_description: str | None = None
    body: str | None = None
    cover_url: str | None = None
    year: int | None = None
    customer_name: str | None = None
    location: str | None = None
    images: list[dict] = []
    updated_at: datetime


class PublicationOut(SeoOut):
    id: int
    slug: str
    title: str
    short_description: str | None = None
    body: str | None = None
    cover_url: str | None = None
    published_at: datetime | None = None
    updated_at: datetime


class RedirectOut(BaseModel):
    old_path: str
    new_path: str
    status_code: int


class SitemapEntry(BaseModel):
    path: str
    updated_at: datetime | None = None
    priority: float = 0.5


class HomeOut(BaseModel):
    settings: SiteSettingsOut
    featured_categories: list[dict]
    featured_equipment: list[dict]
    services: list[ServiceOut]
    projects: list[ProjectOut]
    publications: list[PublicationOut]


SiteSettingsOut.model_rebuild()

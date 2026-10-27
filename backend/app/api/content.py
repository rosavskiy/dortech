from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_session
from app.core.files import file_url
from app.core.pagination import Paginated, to_int
from app.models import Category, Equipment, Page, Project, Publication, Redirect, Service, SiteSettings
from app.schemas.content import (
    HomeOut,
    PageBrief,
    PageOut,
    ProjectOut,
    PublicationOut,
    RedirectOut,
    ServiceOut,
    SitemapEntry,
    SiteSettingsOut,
)
from app.services import catalog as catalog_svc
from app.services.catalog import EQUIPMENT_LOAD

router = APIRouter(prefix="/content", tags=["content"])


def _seo(obj) -> dict:
    return {
        "meta_title": obj.meta_title,
        "meta_description": obj.meta_description,
        "og_image_url": file_url(obj.og_image),
        "noindex": obj.noindex,
    }


def service_out(s: Service) -> ServiceOut:
    return ServiceOut(
        id=s.id,
        slug=s.slug,
        title=s.title,
        short_description=s.short_description,
        body=s.body,
        cover_url=file_url(s.cover),
        icon=s.icon,
        updated_at=s.updated_at,
        **_seo(s),
    )


def project_out(p: Project) -> ProjectOut:
    return ProjectOut(
        id=p.id,
        slug=p.slug,
        title=p.title,
        short_description=p.short_description,
        body=p.body,
        cover_url=file_url(p.cover),
        year=p.year,
        customer_name=p.customer_name,
        location=p.location,
        images=[{"url": file_url(i.file), "alt": i.alt} for i in p.images if file_url(i.file)],
        updated_at=p.updated_at,
        **_seo(p),
    )


def publication_out(p: Publication) -> PublicationOut:
    return PublicationOut(
        id=p.id,
        slug=p.slug,
        title=p.title,
        short_description=p.short_description,
        body=p.body,
        cover_url=file_url(p.cover),
        published_at=p.published_at,
        updated_at=p.updated_at,
        **_seo(p),
    )


async def get_settings_out(session: AsyncSession) -> SiteSettingsOut:
    s = (await session.execute(select(SiteSettings).limit(1))).scalar_one_or_none() or SiteSettings()
    pages = (
        (
            await session.execute(
                select(Page)
                .where(Page.is_published.is_(True), Page.show_in_footer.is_(True))
                .order_by(Page.sort, Page.title)
            )
        )
        .scalars()
        .all()
    )
    return SiteSettingsOut(
        company_name=s.company_name,
        phone=s.phone,
        email=s.email,
        address=s.address,
        working_hours=s.working_hours,
        map_embed=s.map_embed,
        hero_title=s.hero_title,
        hero_subtitle=s.hero_subtitle,
        hero_image_url=file_url(s.hero_image),
        about_short=s.about_short,
        stats=s.stats,
        footer_text=s.footer_text,
        default_meta_title=s.default_meta_title,
        default_meta_description=s.default_meta_description,
        footer_pages=[PageBrief(slug=p.slug, title=p.title) for p in pages],
    )


@router.get("/settings", response_model=SiteSettingsOut)
async def site_settings(session: AsyncSession = Depends(get_session)):
    return await get_settings_out(session)


@router.get("/home", response_model=HomeOut)
async def home(session: AsyncSession = Depends(get_session)):
    cats = [c for c in await catalog_svc.list_categories(session) if c.is_featured or c.parent_id is None][:8]
    eq = (
        (
            await session.execute(
                select(Equipment)
                .options(*EQUIPMENT_LOAD)
                .where(Equipment.is_published.is_(True), Equipment.is_featured.is_(True))
                .order_by(Equipment.sort, Equipment.name)
                .limit(8)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    services = (
        (await session.execute(select(Service).where(Service.is_published.is_(True)).order_by(Service.sort).limit(6)))
        .scalars()
        .all()
    )
    projects = (
        (
            await session.execute(
                select(Project)
                .options(selectinload(Project.images))
                .where(Project.is_published.is_(True))
                .order_by(Project.sort, Project.year.desc())
                .limit(6)
            )
        )
        .scalars()
        .all()
    )
    pubs = (
        (
            await session.execute(
                select(Publication)
                .where(Publication.is_published.is_(True))
                .order_by(Publication.published_at.desc().nulls_last())
                .limit(3)
            )
        )
        .scalars()
        .all()
    )
    return HomeOut(
        settings=await get_settings_out(session),
        featured_categories=[c.model_dump() for c in cats],
        featured_equipment=[catalog_svc.equipment_card(e).model_dump() for e in eq],
        services=[service_out(s) for s in services],
        projects=[project_out(p) for p in projects],
        publications=[publication_out(p) for p in pubs],
    )


@router.get("/pages/{slug}", response_model=PageOut)
async def page(slug: str, session: AsyncSession = Depends(get_session)):
    p = (await session.execute(select(Page).where(Page.slug == slug, Page.is_published.is_(True)))).scalar_one_or_none()
    if p is None:
        raise HTTPException(404, "Страница не найдена")
    return PageOut(slug=p.slug, title=p.title, body=p.body, updated_at=p.updated_at, **_seo(p))


@router.get("/services", response_model=list[ServiceOut])
async def services(session: AsyncSession = Depends(get_session)):
    rows = (
        (
            await session.execute(
                select(Service).where(Service.is_published.is_(True)).order_by(Service.sort, Service.title)
            )
        )
        .scalars()
        .all()
    )
    return [service_out(s) for s in rows]


@router.get("/services/{slug}", response_model=ServiceOut)
async def service(slug: str, session: AsyncSession = Depends(get_session)):
    s = (
        await session.execute(select(Service).where(Service.slug == slug, Service.is_published.is_(True)))
    ).scalar_one_or_none()
    if s is None:
        raise HTTPException(404, "Услуга не найдена")
    return service_out(s)


@router.get("/projects", response_model=list[ProjectOut])
async def projects(session: AsyncSession = Depends(get_session)):
    rows = (
        (
            await session.execute(
                select(Project)
                .options(selectinload(Project.images))
                .where(Project.is_published.is_(True))
                .order_by(Project.sort, Project.year.desc().nulls_last())
            )
        )
        .scalars()
        .all()
    )
    return [project_out(p) for p in rows]


@router.get("/projects/{slug}", response_model=ProjectOut)
async def project(slug: str, session: AsyncSession = Depends(get_session)):
    p = (
        await session.execute(
            select(Project)
            .options(selectinload(Project.images))
            .where(Project.slug == slug, Project.is_published.is_(True))
        )
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(404, "Проект не найден")
    return project_out(p)


@router.get("/publications", response_model=Paginated[PublicationOut])
async def publications(page: str | None = None, session: AsyncSession = Depends(get_session)):
    page_n = to_int(page, 1)
    size = 12
    base = select(Publication).where(Publication.is_published.is_(True))
    total = len((await session.execute(select(Publication.id).where(Publication.is_published.is_(True)))).all())
    pages = max((total + size - 1) // size, 1)
    page_n = min(page_n, pages)
    rows = (
        (
            await session.execute(
                base.order_by(Publication.published_at.desc().nulls_last()).offset((page_n - 1) * size).limit(size)
            )
        )
        .scalars()
        .all()
    )
    return Paginated(items=[publication_out(p) for p in rows], page=page_n, page_size=size, total=total, pages=pages)


@router.get("/publications/{slug}", response_model=PublicationOut)
async def publication(slug: str, session: AsyncSession = Depends(get_session)):
    p = (
        await session.execute(select(Publication).where(Publication.slug == slug, Publication.is_published.is_(True)))
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(404, "Публикация не найдена")
    return publication_out(p)


@router.get("/redirects", response_model=list[RedirectOut])
async def redirects(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Redirect).where(Redirect.is_active.is_(True)))).scalars().all()
    return [RedirectOut(old_path=r.old_path, new_path=r.new_path, status_code=r.status_code) for r in rows]


@router.get("/sitemap", response_model=list[SitemapEntry])
async def sitemap(session: AsyncSession = Depends(get_session)):
    now = datetime.now(UTC)
    out = [
        SitemapEntry(path="/", updated_at=now, priority=1.0),
        SitemapEntry(path="/catalog", updated_at=now, priority=0.9),
        SitemapEntry(path="/services", updated_at=now, priority=0.7),
        SitemapEntry(path="/projects", updated_at=now, priority=0.6),
        SitemapEntry(path="/publications", updated_at=now, priority=0.6),
        SitemapEntry(path="/contacts", updated_at=now, priority=0.6),
    ]
    for c in (await session.execute(select(Category).where(Category.is_published.is_(True)))).scalars():
        out.append(SitemapEntry(path=f"/catalog/{c.slug}", updated_at=c.updated_at, priority=0.8))
    for e in (
        await session.execute(
            select(Equipment.slug, Equipment.updated_at).where(
                Equipment.is_published.is_(True), Equipment.noindex.is_(False)
            )
        )
    ).all():
        out.append(SitemapEntry(path=f"/equipment/{e.slug}", updated_at=e.updated_at, priority=0.7))
    for model, prefix in ((Service, "/services/"), (Project, "/projects/"), (Publication, "/publications/")):
        for row in (
            await session.execute(
                select(model.slug, model.updated_at).where(model.is_published.is_(True), model.noindex.is_(False))
            )
        ).all():
            out.append(SitemapEntry(path=prefix + row.slug, updated_at=row.updated_at, priority=0.5))
    for p in (
        await session.execute(
            select(Page.slug, Page.updated_at).where(Page.is_published.is_(True), Page.noindex.is_(False))
        )
    ).all():
        out.append(SitemapEntry(path=f"/{p.slug}", updated_at=p.updated_at, priority=0.4))
    return out

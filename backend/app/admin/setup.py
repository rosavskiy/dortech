from starlette_admin import I18nConfig, Link, TimezoneConfig
from starlette_admin.contrib.sqla import Admin

from app.admin import views as v
from app.admin.auth import StaffAuthProvider
from app.core.config import settings
from app.core.db import SessionLocal
from app.models import (
    Attachment,
    AttributeDefinition,
    AttributeOption,
    AttributeValue,
    AuditLog,
    AvailabilityStatus,
    Category,
    ContactMessage,
    Equipment,
    EquipmentImage,
    ExtraService,
    ImportJob,
    Inquiry,
    InquiryComment,
    InquiryItem,
    InquiryStatusHistory,
    Manufacturer,
    Organization,
    OutboundMessage,
    Page,
    PricingSettings,
    Project,
    ProjectImage,
    Publication,
    Redirect,
    Service,
    SiteSettings,
    Tariff,
    User,
    WebhookDelivery,
    WebhookEndpoint,
)


def create_admin() -> Admin:
    admin = Admin(
        session_provider=SessionLocal,
        title="Дортех — панель управления",
        base_url=f"/{settings.admin_url_path.strip('/')}",
        route_name="admin",
        auth_provider=StaffAuthProvider(),
        secret_key=settings.secret_key,
        i18n_config=I18nConfig(default_locale="ru", language_switcher=["ru", "en"]),
        timezone_config=TimezoneConfig(default_timezone="Europe/Samara"),
    )
    # Заявки
    admin.add_view(
        v.InquiryView(Inquiry, icon="fa fa-file-lines", display_name="Заявки", menu_label="Заявки", key="inquiry")
    )
    admin.add_view(
        v.InquiryItemView(
            InquiryItem,
            icon="fa fa-list",
            display_name="Позиции заявок",
            menu_label="Позиции заявок",
            key="inquiry-item",
        )
    )
    admin.add_view(
        v.InquiryStatusHistoryView(
            InquiryStatusHistory,
            icon="fa fa-clock-rotate-left",
            display_name="История статусов",
            menu_label="История статусов",
            key="inquiry-status-history",
        )
    )
    admin.add_view(
        v.InquiryCommentView(
            InquiryComment,
            icon="fa fa-comments",
            display_name="Комментарии к заявкам",
            menu_label="Комментарии к заявкам",
            key="inquiry-comment",
        )
    )
    admin.add_view(
        v.AttachmentView(
            Attachment, icon="fa fa-paperclip", display_name="Файлы заявок", menu_label="Файлы заявок", key="attachment"
        )
    )
    admin.add_view(
        v.ContactMessageView(
            ContactMessage,
            icon="fa fa-envelope",
            display_name="Сообщения с сайта",
            menu_label="Сообщения с сайта",
            key="contact-message",
        )
    )
    # Клиенты
    admin.add_view(
        v.OrganizationView(
            Organization,
            icon="fa fa-building",
            display_name="Организации",
            menu_label="Организации",
            key="organization",
        )
    )
    admin.add_view(
        v.UserView(User, icon="fa fa-users", display_name="Пользователи", menu_label="Пользователи", key="user")
    )
    # Каталог
    admin.add_view(
        v.EquipmentView(Equipment, icon="fa fa-truck", display_name="Техника", menu_label="Техника", key="equipment")
    )
    admin.add_view(
        v.EquipmentImageView(
            EquipmentImage,
            icon="fa fa-image",
            display_name="Изображения техники",
            menu_label="Изображения техники",
            key="equipment-image",
        )
    )
    admin.add_view(
        v.TariffView(Tariff, icon="fa fa-ruble-sign", display_name="Тарифы", menu_label="Тарифы", key="tariff")
    )
    admin.add_view(
        v.AttributeValueView(
            AttributeValue,
            icon="fa fa-sliders",
            display_name="Значения характеристик",
            menu_label="Значения характеристик",
            key="attribute-value",
        )
    )
    admin.add_view(
        v.CategoryView(
            Category, icon="fa fa-folder-tree", display_name="Категории", menu_label="Категории", key="category"
        )
    )
    admin.add_view(
        v.ManufacturerView(
            Manufacturer,
            icon="fa fa-industry",
            display_name="Производители",
            menu_label="Производители",
            key="manufacturer",
        )
    )
    admin.add_view(
        v.AvailabilityStatusView(
            AvailabilityStatus,
            icon="fa fa-circle-check",
            display_name="Статусы доступности",
            menu_label="Статусы доступности",
            key="availability-status",
        )
    )
    admin.add_view(
        v.AttributeDefinitionView(
            AttributeDefinition,
            icon="fa fa-tags",
            display_name="Характеристики (словарь)",
            menu_label="Характеристики (словарь)",
            key="attribute-definition",
        )
    )
    admin.add_view(
        v.AttributeOptionView(
            AttributeOption,
            icon="fa fa-list-check",
            display_name="Варианты характеристик",
            menu_label="Варианты характеристик",
            key="attribute-option",
        )
    )
    admin.add_view(
        v.ExtraServiceView(
            ExtraService,
            icon="fa fa-plus-circle",
            display_name="Дополнительные услуги",
            menu_label="Дополнительные услуги",
            key="extra-service",
        )
    )
    admin.add_view(
        v.PricingSettingsView(
            PricingSettings,
            icon="fa fa-calculator",
            display_name="Настройки расчёта",
            menu_label="Настройки расчёта",
            key="pricing-settings",
        )
    )
    # Контент
    admin.add_view(
        v.SiteSettingsView(
            SiteSettings,
            icon="fa fa-gear",
            display_name="Настройки сайта",
            menu_label="Настройки сайта",
            key="site-settings",
        )
    )
    admin.add_view(v.PageView(Page, icon="fa fa-file", display_name="Страницы", menu_label="Страницы", key="page"))
    admin.add_view(
        v.ServiceView(Service, icon="fa fa-briefcase", display_name="Услуги", menu_label="Услуги", key="service")
    )
    admin.add_view(
        v.ProjectView(
            Project, icon="fa fa-diagram-project", display_name="Проекты", menu_label="Проекты", key="project"
        )
    )
    admin.add_view(
        v.ProjectImageView(
            ProjectImage,
            icon="fa fa-images",
            display_name="Фото проектов",
            menu_label="Фото проектов",
            key="project-image",
        )
    )
    admin.add_view(
        v.PublicationView(
            Publication, icon="fa fa-newspaper", display_name="Публикации", menu_label="Публикации", key="publication"
        )
    )
    admin.add_view(
        v.RedirectView(
            Redirect, icon="fa fa-arrow-right", display_name="Редиректы", menu_label="Редиректы", key="redirect"
        )
    )
    # Обмен и журнал
    admin.add_view(
        Link(
            menu_label="Импорт CSV (кабинет) ↗",
            icon="fa fa-file-csv",
            url=f"{settings.site_url}/manager/import",
            target="_blank",
        )
    )
    admin.add_view(
        v.ImportJobView(
            ImportJob,
            icon="fa fa-file-import",
            display_name="Импорт CSV: журнал",
            menu_label="Импорт CSV: журнал",
            key="import-job",
        )
    )
    admin.add_view(
        v.WebhookEndpointView(
            WebhookEndpoint,
            icon="fa fa-plug",
            display_name="Webhook: приёмники",
            menu_label="Webhook: приёмники",
            key="webhook-endpoint",
        )
    )
    admin.add_view(
        v.OutboundMessageView(
            OutboundMessage,
            icon="fa fa-paper-plane",
            display_name="Исходящие (email, webhook)",
            menu_label="Исходящие (email, webhook)",
            key="outbound-message",
        )
    )
    admin.add_view(
        v.WebhookDeliveryView(
            WebhookDelivery,
            icon="fa fa-inbox",
            display_name="Webhook: тестовый приёмник",
            menu_label="Webhook: тестовый приёмник",
            key="webhook-delivery",
        )
    )
    admin.add_view(
        v.AuditLogView(
            AuditLog, icon="fa fa-shield", display_name="Журнал действий", menu_label="Журнал действий", key="audit-log"
        )
    )
    return admin

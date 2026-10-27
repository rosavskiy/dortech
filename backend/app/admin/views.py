from typing import Any

from starlette.requests import Request
from starlette_admin import (
    BooleanField,
    DateTimeField,
    DecimalField,
    EnumField,
    FileField,
    HasMany,
    HasOne,
    ImageField,
    IntegerField,
    JSONField,
    PasswordField,
    StringField,
    TextAreaField,
    TinyMCEEditorField,
)
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

from app.admin.auth import role_of
from app.core.config import settings
from app.core.security import hash_password
from app.models import (
    STATUS_LABELS,
    AuditLog,
    Role,
)

media = LocalStorage(base_dir=settings.media_root / "public", name="media")

TINY = dict(
    height=360,
    menubar=False,
    toolbar="undo redo | blocks | bold italic | bullist numlist | link image table | removeformat",
)

SEO_FIELDS = [
    StringField("meta_title", label="SEO: заголовок (title)", exclude_from_list=True),
    TextAreaField("meta_description", label="SEO: описание (description)", exclude_from_list=True),
    ImageField(
        "og_image", label="SEO: изображение для соцсетей", storage=media, upload_folder="og", exclude_from_list=True
    ),
    BooleanField("noindex", label="Не индексировать", exclude_from_list=True),
]


class AuditMixin:
    """Запись существенных изменений в журнал (ТЗ 4.3)."""

    audit_target = True

    async def _audit(self, request: Request, action: str, obj: Any, changes: dict | None = None) -> None:
        if not getattr(self, "audit_target", False):
            return
        session = request.state.session
        user = getattr(request.state, "current_user", None)
        session.add(
            AuditLog(
                actor_id=getattr(user, "id", None),
                actor_repr=str(user) if user else "панель",
                action=action,
                target_type=type(obj).__name__,
                target_id=str(getattr(obj, "id", "")),
                object_repr=str(obj)[:255],
                changes=changes,
                ip=request.client.host if request.client else None,
            )
        )
        await session.commit()

    async def after_create(self, request: Request, obj: Any) -> None:
        await self._audit(request, "create", obj)

    async def after_edit(self, request: Request, obj: Any) -> None:
        await self._audit(request, "update", obj)

    async def after_delete(self, request: Request, obj: Any) -> None:
        await self._audit(request, "delete", obj)


class AdminOnly:
    def is_accessible(self, request: Request) -> bool:
        return role_of(request) == Role.admin


class StaffAccess:
    def is_accessible(self, request: Request) -> bool:
        return role_of(request) in (Role.admin, Role.manager)

    def can_create(self, request: Request) -> bool:
        return role_of(request) == Role.admin

    def can_delete(self, request: Request) -> bool:
        return role_of(request) == Role.admin


# ---------- пользователи и организации ----------


class UserView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("email", label="Email", required=True),
        PasswordField(
            "password_hash",
            label="Пароль (введите новый, чтобы сменить)",
            exclude_from_list=True,
            exclude_from_detail=True,
        ),
        StringField("last_name", label="Фамилия"),
        StringField("first_name", label="Имя"),
        StringField("patronymic", label="Отчество", exclude_from_list=True),
        StringField("phone", label="Телефон"),
        StringField("position", label="Должность", exclude_from_list=True),
        EnumField(
            "role",
            label="Роль",
            enum=Role,
            choices=[("client", "Клиент"), ("manager", "Менеджер"), ("admin", "Администратор")],
        ),
        HasOne("organization", key="organization", label="Организация"),
        BooleanField("is_active", label="Активен"),
        DateTimeField("email_confirmed_at", label="Email подтверждён", exclude_from_list=True),
        DateTimeField("blocked_at", label="Заблокирован с"),
        TextAreaField("blocked_reason", label="Причина блокировки", exclude_from_list=True),
        DateTimeField(
            "last_login_at", label="Последний вход", read_only=True, exclude_from_create=True, exclude_from_edit=True
        ),
    ]
    searchable_fields = ["email", "last_name", "first_name", "phone"]
    fields_default_sort = [("id", True)]

    async def before_create(self, request: Request, data: dict, obj: Any) -> None:
        if data.get("password_hash"):
            obj.password_hash = hash_password(data["password_hash"])
        obj.email = obj.email.strip().lower()

    async def before_edit(self, request: Request, data: dict, obj: Any) -> None:
        pwd = data.get("password_hash")
        if pwd and not str(pwd).startswith("$argon2"):
            obj.password_hash = hash_password(pwd)
        obj.email = obj.email.strip().lower()
        if obj.blocked_at:
            from sqlalchemy import delete

            from app.models import UserSession

            await request.state.session.execute(delete(UserSession).where(UserSession.user_id == obj.id))


class OrganizationView(StaffAccess, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        StringField("inn", label="ИНН"),
        StringField("kpp", label="КПП", exclude_from_list=True),
        TextAreaField("legal_address", label="Юридический адрес", exclude_from_list=True),
        StringField("phone", label="Телефон"),
        StringField("email", label="Email"),
        TextAreaField("note", label="Примечание", exclude_from_list=True),
        HasMany("users", key="user", label="Пользователи", exclude_from_create=True, exclude_from_edit=True),
    ]
    searchable_fields = ["name", "inn", "email"]


# ---------- каталог ----------


class CategoryView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        HasOne("parent", key="category", label="Родительская категория"),
        TextAreaField("description", label="Описание", exclude_from_list=True),
        ImageField("image", label="Изображение", storage=media, upload_folder="categories"),
        IntegerField("sort", label="Порядок"),
        BooleanField("is_featured", label="На главной"),
        BooleanField("is_published", label="Опубликована"),
        HasMany("attributes", key="attribute-definition", label="Характеристики категории", exclude_from_list=True),
        *SEO_FIELDS,
    ]
    searchable_fields = ["name", "slug"]
    fields_default_sort = ["sort", "name"]


class ManufacturerView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        ImageField("logo", label="Логотип", storage=media, upload_folder="manufacturers"),
        IntegerField("sort", label="Порядок"),
    ]
    searchable_fields = ["name"]


class AvailabilityStatusView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("code", label="Код", required=True),
        StringField("name", label="Название", required=True),
        StringField("color", label="Цвет (green/orange/gray/red)"),
        BooleanField("allow_request", label="Можно добавить в заявку"),
        IntegerField("sort", label="Порядок"),
    ]


class AttributeDefinitionView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("code", label="Код (латиница)", required=True),
        StringField("name", label="Название", required=True),
        StringField("unit", label="Единица"),
        EnumField(
            "type",
            label="Тип",
            choices=[("number", "Число"), ("string", "Строка"), ("bool", "Да/нет"), ("choice", "Выбор из списка")],
        ),
        BooleanField("is_filterable", label="Фильтр в каталоге"),
        BooleanField("is_comparable", label="В сравнении"),
        IntegerField("sort", label="Порядок"),
        HasMany("categories", key="category", label="Категории"),
        HasMany(
            "options",
            key="attribute-option",
            label="Варианты (для типа «выбор»)",
            exclude_from_create=True,
            exclude_from_edit=True,
        ),
    ]
    searchable_fields = ["code", "name"]
    fields_default_sort = ["sort"]


class AttributeOptionView(AdminOnly, ModelView):
    fields = [
        "id",
        HasOne("attribute", key="attribute-definition", label="Характеристика", required=True),
        StringField("value", label="Значение", required=True),
        IntegerField("sort", label="Порядок"),
    ]


class EquipmentView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        StringField("external_id", label="Внешний ID (для CSV)"),
        HasOne("category", key="category", label="Категория", required=True),
        HasOne("manufacturer", key="manufacturer", label="Производитель"),
        StringField("model", label="Модель"),
        IntegerField("year", label="Год выпуска"),
        HasOne("status", key="availability-status", label="Доступность"),
        TextAreaField("short_description", label="Краткое описание", exclude_from_list=True),
        TinyMCEEditorField("description", label="Описание", exclude_from_list=True, **TINY),
        TinyMCEEditorField("terms", label="Условия аренды", exclude_from_list=True, **TINY),
        BooleanField("is_published", label="Опубликована"),
        BooleanField("is_featured", label="На главной"),
        BooleanField("price_hidden", label="Скрыть цену (показывать «запросить предложение»)"),
        IntegerField("sort", label="Порядок", exclude_from_list=True),
        HasOne("tariff", key="tariff", label="Тариф", exclude_from_create=True, exclude_from_edit=True),
        HasMany("images", key="equipment-image", label="Изображения", exclude_from_create=True, exclude_from_edit=True),
        HasMany(
            "attribute_values",
            key="attribute-value",
            label="Характеристики",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_list=True,
        ),
        *SEO_FIELDS,
    ]
    searchable_fields = ["name", "model", "slug", "external_id"]
    fields_default_sort = ["sort", "name"]
    page_size = 50


class EquipmentImageView(AdminOnly, ModelView):
    fields = [
        "id",
        HasOne("equipment", key="equipment", label="Техника", required=True),
        ImageField("file", label="Файл", storage=media, upload_folder="equipment", required=True),
        StringField("alt", label="Подпись (alt)"),
        IntegerField("sort", label="Порядок"),
    ]


class AttributeValueView(AdminOnly, ModelView):
    fields = [
        "id",
        HasOne("equipment", key="equipment", label="Техника", required=True),
        HasOne("attribute", key="attribute-definition", label="Характеристика", required=True),
        DecimalField("value_number", label="Число"),
        StringField("value_text", label="Текст"),
        BooleanField("value_bool", label="Да/нет"),
        HasOne("option", key="attribute-option", label="Вариант (для типа «выбор»)"),
    ]


class TariffView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        HasOne("equipment", key="equipment", label="Техника", required=True),
        DecimalField("price_per_shift", label="Цена за смену, ₽"),
        DecimalField("price_per_day", label="Цена за сутки, ₽"),
        IntegerField("shift_hours", label="Часов в смене"),
        IntegerField("min_units", label="Минимум смен/суток"),
        TextAreaField("note", label="Примечание", exclude_from_list=True),
    ]


class ExtraServiceView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        TextAreaField("description", label="Описание", exclude_from_list=True),
        DecimalField("price", label="Цена, ₽ (фиксированная за заявку)"),
        BooleanField("is_active", label="Активна"),
        IntegerField("sort", label="Порядок"),
    ]


class PricingSettingsView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        IntegerField("rounding_step", label="Шаг округления, ₽ (1 / 10 / 100)"),
        StringField("vat_label", label="Пометка о НДС"),
        TextAreaField("disclaimer_text", label="Текст оговорки о расчёте"),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


# ---------- контент ----------


class PageView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("title", label="Заголовок", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        TinyMCEEditorField("body", label="Текст", exclude_from_list=True, **TINY),
        BooleanField("is_published", label="Опубликована"),
        BooleanField("show_in_footer", label="Ссылка в подвале"),
        IntegerField("sort", label="Порядок"),
        *SEO_FIELDS,
    ]
    searchable_fields = ["title", "slug"]


class ServiceView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("title", label="Название", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        TextAreaField("short_description", label="Краткое описание", exclude_from_list=True),
        TinyMCEEditorField("body", label="Текст", exclude_from_list=True, **TINY),
        ImageField("cover", label="Обложка", storage=media, upload_folder="services"),
        StringField("icon", label="Иконка (код)", exclude_from_list=True),
        BooleanField("is_published", label="Опубликована"),
        IntegerField("sort", label="Порядок"),
        *SEO_FIELDS,
    ]
    searchable_fields = ["title"]
    fields_default_sort = ["sort"]


class ProjectView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("title", label="Название", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        IntegerField("year", label="Год"),
        StringField("customer_name", label="Заказчик"),
        StringField("location", label="Место", exclude_from_list=True),
        TextAreaField("short_description", label="Краткое описание", exclude_from_list=True),
        TinyMCEEditorField("body", label="Текст", exclude_from_list=True, **TINY),
        ImageField("cover", label="Обложка", storage=media, upload_folder="projects"),
        BooleanField("is_published", label="Опубликован"),
        IntegerField("sort", label="Порядок"),
        HasMany("images", key="project-image", label="Галерея", exclude_from_create=True, exclude_from_edit=True),
        *SEO_FIELDS,
    ]
    searchable_fields = ["title", "customer_name"]


class ProjectImageView(AdminOnly, ModelView):
    fields = [
        "id",
        HasOne("project", key="project", label="Проект", required=True),
        ImageField("file", label="Файл", storage=media, upload_folder="projects", required=True),
        StringField("alt", label="Подпись"),
        IntegerField("sort", label="Порядок"),
    ]


class PublicationView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("title", label="Заголовок", required=True),
        StringField("slug", label="Адрес (slug)", required=True),
        DateTimeField("published_at", label="Дата публикации"),
        TextAreaField("short_description", label="Анонс", exclude_from_list=True),
        TinyMCEEditorField("body", label="Текст", exclude_from_list=True, **TINY),
        ImageField("cover", label="Обложка", storage=media, upload_folder="publications"),
        BooleanField("is_published", label="Опубликована"),
        *SEO_FIELDS,
    ]
    searchable_fields = ["title"]
    fields_default_sort = [("published_at", True)]


class SiteSettingsView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("company_name", label="Название компании"),
        StringField("phone", label="Телефон"),
        StringField("email", label="Email"),
        TextAreaField("address", label="Адрес"),
        StringField("working_hours", label="Режим работы"),
        TextAreaField("map_embed", label="Код карты (iframe)", exclude_from_list=True),
        StringField("hero_title", label="Главная: заголовок", exclude_from_list=True),
        TextAreaField("hero_subtitle", label="Главная: подзаголовок", exclude_from_list=True),
        ImageField(
            "hero_image", label="Главная: изображение", storage=media, upload_folder="site", exclude_from_list=True
        ),
        TextAreaField("about_short", label="Коротко о компании", exclude_from_list=True),
        JSONField(
            "stats",
            label='Цифры на главной (JSON: [{"value": "15+", "label": "лет на рынке"}])',
            exclude_from_list=True,
        ),
        TextAreaField("footer_text", label="Текст в подвале", exclude_from_list=True),
        StringField("default_meta_title", label="SEO: title по умолчанию", exclude_from_list=True),
        TextAreaField("default_meta_description", label="SEO: description по умолчанию", exclude_from_list=True),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class RedirectView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("old_path", label="Старый адрес (путь)", required=True),
        StringField("new_path", label="Новый адрес", required=True),
        IntegerField("status_code", label="Код (301/302)"),
        BooleanField("is_active", label="Активен"),
    ]
    searchable_fields = ["old_path", "new_path"]


# ---------- заявки ----------

STATUS_CHOICES = [(k.value, v) for k, v in STATUS_LABELS.items()]


class InquiryView(StaffAccess, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("number", label="Номер", read_only=True),
        EnumField("status", label="Статус", choices=STATUS_CHOICES),
        DateTimeField("created_at", label="Создана", read_only=True, exclude_from_create=True, exclude_from_edit=True),
        HasOne("organization", key="organization", label="Организация"),
        StringField("company_name_raw", label="Компания (из формы)"),
        StringField("contact_name", label="Контактное лицо", required=True),
        StringField("contact_phone", label="Телефон", required=True),
        StringField("contact_email", label="Email"),
        StringField("period_from", label="Период с", exclude_from_list=True),
        StringField("period_to", label="Период по", exclude_from_list=True),
        TextAreaField("work_place", label="Место работ", exclude_from_list=True),
        TextAreaField("comment", label="Комментарий клиента", exclude_from_list=True),
        HasOne("assigned_to", key="user", label="Ответственный"),
        DecimalField("estimated_total", label="Предварительная сумма, ₽", read_only=True),
        EnumField(
            "source",
            label="Источник",
            choices=[("web", "Сайт"), ("account", "Кабинет"), ("repeat", "Повтор")],
            read_only=True,
        ),
        HasMany(
            "items",
            key="inquiry-item",
            label="Позиции",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_list=True,
        ),
        HasMany(
            "status_history",
            key="inquiry-status-history",
            label="История статусов",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_list=True,
        ),
        HasMany(
            "comments",
            key="inquiry-comment",
            label="Комментарии",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_list=True,
        ),
        HasMany(
            "attachments",
            key="attachment",
            label="Файлы",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_list=True,
        ),
        JSONField(
            "estimate_snapshot",
            label="Снимок расчёта",
            read_only=True,
            exclude_from_list=True,
            exclude_from_create=True,
        ),
    ]
    searchable_fields = ["number", "contact_name", "contact_phone", "contact_email", "company_name_raw"]
    fields_default_sort = [("created_at", True)]
    page_size = 50

    def can_create(self, request: Request) -> bool:
        return False

    async def before_edit(self, request: Request, data: dict, obj: Any) -> None:
        # фиксируем смену статуса в истории
        from app.models import InquiryStatus, InquiryStatusHistory

        old = getattr(obj, "_prev_status", None)
        new = data.get("status")
        if new and old and new != old:
            request.state.session.add(
                InquiryStatusHistory(
                    inquiry_id=obj.id,
                    from_status=InquiryStatus(old),
                    to_status=InquiryStatus(new),
                    changed_by_id=getattr(getattr(request.state, "current_user", None), "id", None),
                    comment="Изменено в панели",
                )
            )


class InquiryItemView(StaffAccess, ModelView):
    fields = [
        "id",
        HasOne("inquiry", key="inquiry", label="Заявка"),
        HasOne("equipment", key="equipment", label="Техника"),
        StringField("name_snapshot", label="Название"),
        IntegerField("quantity", label="Кол-во"),
        IntegerField("units", label="Смен/суток"),
        EnumField("unit", label="Единица", choices=[("shift", "смена"), ("day", "сутки")]),
        DecimalField("unit_price_snapshot", label="Цена за единицу"),
        DecimalField("line_total", label="Сумма"),
        BooleanField("needs_quote", label="По запросу"),
    ]


class InquiryStatusHistoryView(StaffAccess, ModelView):
    fields = [
        "id",
        HasOne("inquiry", key="inquiry", label="Заявка"),
        EnumField("from_status", label="Из", choices=STATUS_CHOICES),
        EnumField("to_status", label="В", choices=STATUS_CHOICES),
        HasOne("changed_by", key="user", label="Кто"),
        TextAreaField("comment", label="Комментарий"),
        DateTimeField("created_at", label="Когда"),
    ]
    fields_default_sort = [("created_at", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class InquiryCommentView(StaffAccess, ModelView):
    fields = [
        "id",
        HasOne("inquiry", key="inquiry", label="Заявка"),
        HasOne("author", key="user", label="Автор"),
        TextAreaField("text", label="Текст", required=True),
        BooleanField("is_internal", label="Внутренний (не виден клиенту)"),
        DateTimeField("created_at", label="Когда", read_only=True, exclude_from_create=True, exclude_from_edit=True),
    ]
    fields_default_sort = [("created_at", True)]


class AttachmentView(StaffAccess, ModelView):
    fields = [
        "id",
        HasOne("inquiry", key="inquiry", label="Заявка"),
        HasOne("organization", key="organization", label="Организация"),
        StringField("original_name", label="Файл"),
        StringField("content_type", label="Тип"),
        IntegerField("size", label="Размер, байт"),
        EnumField(
            "kind", label="Вид", choices=[("client_doc", "Документ клиента"), ("offer_pdf", "Предложение (PDF)")]
        ),
        HasOne("uploaded_by", key="user", label="Загрузил"),
        DateTimeField("created_at", label="Когда"),
    ]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class ContactMessageView(StaffAccess, ModelView):
    fields = [
        "id",
        StringField("name", label="Имя"),
        StringField("phone", label="Телефон"),
        StringField("email", label="Email"),
        TextAreaField("text", label="Сообщение"),
        BooleanField("is_processed", label="Обработано"),
        DateTimeField("created_at", label="Когда", read_only=True),
    ]
    fields_default_sort = [("created_at", True)]

    def can_create(self, request: Request) -> bool:
        return False


# ---------- обмен и журнал ----------


class ImportJobView(AdminOnly, ModelView):
    fields = [
        "id",
        StringField("file_name", label="Файл"),
        BooleanField("dry_run", label="Только проверка"),
        EnumField(
            "status", label="Статус", choices=[("pending", "Выполняется"), ("done", "Готово"), ("failed", "Ошибка")]
        ),
        IntegerField("total", label="Строк"),
        IntegerField("created", label="Создано"),
        IntegerField("updated", label="Обновлено"),
        IntegerField("skipped", label="Пропущено"),
        IntegerField("failed", label="С ошибками"),
        JSONField("errors", label="Ошибки", exclude_from_list=True),
        StringField("report_file", label="Отчёт"),
        HasOne("started_by", key="user", label="Запустил"),
        DateTimeField("created_at", label="Начало"),
        DateTimeField("finished_at", label="Конец"),
    ]
    fields_default_sort = [("created_at", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class WebhookEndpointView(AdminOnly, AuditMixin, ModelView):
    fields = [
        "id",
        StringField("name", label="Название", required=True),
        StringField("url", label="URL", required=True),
        PasswordField("secret", label="Секрет подписи", required=True, exclude_from_list=True),
        BooleanField("is_active", label="Активен"),
        JSONField("events", label="События (JSON-список)", exclude_from_list=True),
    ]


class OutboundMessageView(AdminOnly, ModelView):
    fields = [
        "id",
        EnumField("kind", label="Тип", choices=[("email", "Email"), ("webhook", "Webhook")]),
        StringField("event", label="Событие"),
        EnumField(
            "status", label="Статус", choices=[("pending", "В очереди"), ("sent", "Отправлено"), ("failed", "Ошибка")]
        ),
        IntegerField("attempts", label="Попыток"),
        DateTimeField("next_attempt_at", label="Следующая попытка"),
        IntegerField("response_code", label="Код ответа"),
        TextAreaField("last_error", label="Последняя ошибка", exclude_from_list=True),
        JSONField("payload", label="Данные", exclude_from_list=True),
        DateTimeField("created_at", label="Создано"),
        DateTimeField("sent_at", label="Отправлено"),
    ]
    fields_default_sort = [("created_at", True)]

    def can_create(self, request: Request) -> bool:
        return False


class WebhookDeliveryView(AdminOnly, ModelView):
    fields = [
        "id",
        DateTimeField("received_at", label="Получено"),
        BooleanField("signature_valid", label="Подпись верна"),
        JSONField("headers", label="Заголовки", exclude_from_list=True),
        JSONField("body", label="Тело", exclude_from_list=True),
    ]
    fields_default_sort = [("received_at", True)]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False


class AuditLogView(AdminOnly, ModelView):
    fields = [
        "id",
        DateTimeField("created_at", label="Когда"),
        StringField("actor_repr", label="Кто"),
        StringField("action", label="Действие"),
        StringField("target_type", label="Объект"),
        StringField("target_id", label="ID"),
        StringField("object_repr", label="Описание"),
        JSONField("changes", label="Изменения", exclude_from_list=True),
        StringField("ip", label="IP"),
    ]
    fields_default_sort = [("created_at", True)]
    searchable_fields = ["actor_repr", "action", "target_type", "object_repr"]

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


__all__ = ["media", "FileField"]

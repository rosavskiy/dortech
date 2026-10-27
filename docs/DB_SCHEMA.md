# Структура базы данных

Генерируется из моделей SQLAlchemy (`backend/app/models`). Миграции — `backend/alembic/versions`. PostgreSQL 16, расширение `pg_trgm`.

## `attachments`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `public_id` | CHAR(32) | unique, index, not null |
| `inquiry_id` | INTEGER | FK → inquiries.id (CASCADE), index, not null |
| `organization_id` | INTEGER | FK → organizations.id (SET NULL), index |
| `uploaded_by_id` | INTEGER | FK → users.id (SET NULL) |
| `path` | VARCHAR(500) | not null |
| `original_name` | VARCHAR(255) | not null |
| `content_type` | VARCHAR(150) | not null |
| `size` | INTEGER | not null |
| `kind` | VARCHAR(20) | not null |
| `created_at` | DATETIME | not null |

Индексы: `ix_attachments_organization_id` (organization_id), `ix_attachments_public_id` (public_id), `ix_attachments_inquiry_id` (inquiry_id)

## `attribute_definitions`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `code` | VARCHAR(50) | unique, not null |
| `name` | VARCHAR(150) | not null |
| `unit` | VARCHAR(30) |  |
| `type` | VARCHAR(20) | not null |
| `is_filterable` | BOOLEAN | not null |
| `is_comparable` | BOOLEAN | not null |
| `sort` | INTEGER | not null |

## `attribute_options`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `attribute_id` | INTEGER | FK → attribute_definitions.id (CASCADE), not null |
| `value` | VARCHAR(150) | not null |
| `sort` | INTEGER | not null |

## `attribute_values`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `equipment_id` | INTEGER | FK → equipment.id (CASCADE), index, not null |
| `attribute_id` | INTEGER | FK → attribute_definitions.id (CASCADE), index, not null |
| `value_number` | NUMERIC(14, 3) | index |
| `value_text` | VARCHAR(255) |  |
| `value_bool` | BOOLEAN |  |
| `option_id` | INTEGER | FK → attribute_options.id (SET NULL), index |

Индексы: `ix_attribute_values_equipment_id` (equipment_id), `ix_attribute_values_attribute_id` (attribute_id), `ix_attribute_values_value_number` (value_number), `ix_attribute_values_option_id` (option_id)

## `audit_log`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `actor_id` | INTEGER | FK → users.id (SET NULL), index |
| `actor_repr` | VARCHAR(255) |  |
| `action` | VARCHAR(50) | index, not null |
| `target_type` | VARCHAR(50) | index, not null |
| `target_id` | VARCHAR(50) | index |
| `object_repr` | VARCHAR(255) |  |
| `changes` | JSONB |  |
| `ip` | VARCHAR(64) |  |
| `created_at` | DATETIME | index, not null |

Индексы: `ix_audit_log_target_type` (target_type), `ix_audit_log_action` (action), `ix_audit_log_created_at` (created_at), `ix_audit_log_actor_id` (actor_id), `ix_audit_log_target_id` (target_id)

## `availability_statuses`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `code` | VARCHAR(50) | unique, not null |
| `name` | VARCHAR(100) | not null |
| `color` | VARCHAR(20) | not null |
| `allow_request` | BOOLEAN | not null |
| `sort` | INTEGER | not null |

## `categories`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `parent_id` | INTEGER | FK → categories.id (SET NULL) |
| `name` | VARCHAR(200) | not null |
| `slug` | VARCHAR(200) | unique, not null |
| `description` | TEXT |  |
| `image` | JSONB |  |
| `sort` | INTEGER | not null |
| `is_featured` | BOOLEAN | not null |
| `is_published` | BOOLEAN | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `category_attributes`

| Колонка | Тип | Ограничения |
|---|---|---|
| `category_id` | INTEGER | PK, FK → categories.id (CASCADE) |
| `attribute_id` | INTEGER | PK, FK → attribute_definitions.id (CASCADE) |

## `contact_messages`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(200) | not null |
| `phone` | VARCHAR(32) |  |
| `email` | VARCHAR(255) |  |
| `text` | TEXT | not null |
| `ip` | VARCHAR(64) |  |
| `is_processed` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |

## `email_tokens`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `user_id` | INTEGER | FK → users.id (CASCADE), index, not null |
| `kind` | VARCHAR(20) | not null |
| `token_hash` | VARCHAR(64) | unique, not null |
| `expires_at` | DATETIME | not null |
| `used_at` | DATETIME |  |
| `created_at` | DATETIME | not null |

Индексы: `ix_email_tokens_user_id` (user_id)

## `equipment`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `external_id` | VARCHAR(100) | unique |
| `name` | VARCHAR(255) | not null |
| `slug` | VARCHAR(255) | unique, not null |
| `category_id` | INTEGER | FK → categories.id (RESTRICT), index, not null |
| `manufacturer_id` | INTEGER | FK → manufacturers.id (SET NULL), index |
| `model` | VARCHAR(150) |  |
| `year` | INTEGER |  |
| `short_description` | TEXT |  |
| `description` | TEXT |  |
| `terms` | TEXT |  |
| `status_id` | INTEGER | FK → availability_statuses.id (SET NULL), index |
| `is_published` | BOOLEAN | index, not null |
| `is_featured` | BOOLEAN | not null |
| `price_hidden` | BOOLEAN | not null |
| `sort` | INTEGER | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

Индексы: `ix_equipment_is_published` (is_published), `ix_equipment_category_id` (category_id), `ix_equipment_status_id` (status_id), `ix_equipment_manufacturer_id` (manufacturer_id)

## `equipment_images`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `equipment_id` | INTEGER | FK → equipment.id (CASCADE), index, not null |
| `file` | JSONB | not null |
| `alt` | VARCHAR(255) |  |
| `sort` | INTEGER | not null |

Индексы: `ix_equipment_images_equipment_id` (equipment_id)

## `extra_services`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(200) | not null |
| `description` | TEXT |  |
| `price` | NUMERIC(12, 2) | not null |
| `is_active` | BOOLEAN | not null |
| `sort` | INTEGER | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `import_jobs`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `file_name` | VARCHAR(255) | not null |
| `dry_run` | BOOLEAN | not null |
| `status` | VARCHAR(20) | not null |
| `total` | INTEGER | not null |
| `created` | INTEGER | not null |
| `updated` | INTEGER | not null |
| `skipped` | INTEGER | not null |
| `failed` | INTEGER | not null |
| `errors` | JSONB |  |
| `report_file` | VARCHAR(500) |  |
| `started_by_id` | INTEGER | FK → users.id (SET NULL) |
| `created_at` | DATETIME | not null |
| `finished_at` | DATETIME |  |

## `inquiries`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `public_id` | CHAR(32) | unique, index, not null |
| `number` | VARCHAR(20) | unique |
| `organization_id` | INTEGER | FK → organizations.id (SET NULL), index |
| `created_by_id` | INTEGER | FK → users.id (SET NULL), index |
| `contact_name` | VARCHAR(200) | not null |
| `contact_phone` | VARCHAR(32) | not null |
| `contact_email` | VARCHAR(255) |  |
| `company_name_raw` | VARCHAR(255) |  |
| `period_from` | DATE |  |
| `period_to` | DATE |  |
| `work_place` | TEXT |  |
| `comment` | TEXT |  |
| `status` | VARCHAR(20) | index, not null |
| `assigned_to_id` | INTEGER | FK → users.id (SET NULL), index |
| `estimated_total` | NUMERIC(14, 2) |  |
| `estimate_snapshot` | JSONB |  |
| `source` | VARCHAR(20) | not null |
| `parent_id` | INTEGER | FK → inquiries.id (SET NULL) |
| `ip` | VARCHAR(64) |  |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

Индексы: `ix_inquiries_created_by_id` (created_by_id), `ix_inquiries_organization_id` (organization_id), `ix_inquiries_status` (status), `ix_inquiries_assigned_to_id` (assigned_to_id), `ix_inquiries_public_id` (public_id)

## `inquiry_comments`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `inquiry_id` | INTEGER | FK → inquiries.id (CASCADE), index, not null |
| `author_id` | INTEGER | FK → users.id (SET NULL) |
| `text` | TEXT | not null |
| `is_internal` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |

Индексы: `ix_inquiry_comments_inquiry_id` (inquiry_id)

## `inquiry_extra_services`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `inquiry_id` | INTEGER | FK → inquiries.id (CASCADE), index, not null |
| `service_id` | INTEGER | FK → extra_services.id (SET NULL) |
| `name_snapshot` | VARCHAR(200) | not null |
| `price_snapshot` | NUMERIC(12, 2) | not null |

Индексы: `ix_inquiry_extra_services_inquiry_id` (inquiry_id)

## `inquiry_items`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `inquiry_id` | INTEGER | FK → inquiries.id (CASCADE), index, not null |
| `equipment_id` | INTEGER | FK → equipment.id (RESTRICT), index, not null |
| `name_snapshot` | VARCHAR(255) | not null |
| `model_snapshot` | VARCHAR(150) |  |
| `quantity` | INTEGER | not null |
| `units` | INTEGER | not null |
| `unit` | VARCHAR(10) | not null |
| `unit_price_snapshot` | NUMERIC(12, 2) |  |
| `line_total` | NUMERIC(14, 2) |  |
| `needs_quote` | BOOLEAN | not null |

Индексы: `ix_inquiry_items_inquiry_id` (inquiry_id), `ix_inquiry_items_equipment_id` (equipment_id)

## `inquiry_status_history`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `inquiry_id` | INTEGER | FK → inquiries.id (CASCADE), index, not null |
| `from_status` | VARCHAR(20) |  |
| `to_status` | VARCHAR(20) | not null |
| `changed_by_id` | INTEGER | FK → users.id (SET NULL) |
| `comment` | TEXT |  |
| `created_at` | DATETIME | not null |

Индексы: `ix_inquiry_status_history_inquiry_id` (inquiry_id)

## `manufacturers`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(200) | unique, not null |
| `slug` | VARCHAR(200) | unique, not null |
| `logo` | JSONB |  |
| `sort` | INTEGER | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `organizations`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(255) | not null |
| `inn` | VARCHAR(12) | index |
| `kpp` | VARCHAR(9) |  |
| `legal_address` | TEXT |  |
| `phone` | VARCHAR(32) |  |
| `email` | VARCHAR(255) |  |
| `note` | TEXT |  |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

Индексы: `ix_organizations_inn` (inn)

## `outbox`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `kind` | VARCHAR(20) | not null |
| `endpoint_id` | INTEGER | FK → webhook_endpoints.id (SET NULL) |
| `event` | VARCHAR(50) |  |
| `delivery_id` | VARCHAR(36) | index |
| `payload` | JSONB | not null |
| `status` | VARCHAR(20) | index, not null |
| `attempts` | INTEGER | not null |
| `next_attempt_at` | DATETIME | index |
| `last_error` | TEXT |  |
| `response_code` | INTEGER |  |
| `created_at` | DATETIME | not null |
| `sent_at` | DATETIME |  |

Индексы: `ix_outbox_delivery_id` (delivery_id), `ix_outbox_next_attempt_at` (next_attempt_at), `ix_outbox_status` (status)

## `pages`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `slug` | VARCHAR(200) | unique, not null |
| `title` | VARCHAR(255) | not null |
| `body` | TEXT |  |
| `is_published` | BOOLEAN | not null |
| `show_in_footer` | BOOLEAN | not null |
| `sort` | INTEGER | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `pricing_settings`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `rounding_step` | INTEGER | not null |
| `vat_label` | VARCHAR(100) | not null |
| `disclaimer_text` | TEXT | not null |

## `project_images`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `project_id` | INTEGER | FK → projects.id (CASCADE), index, not null |
| `file` | JSONB | not null |
| `alt` | VARCHAR(255) |  |
| `sort` | INTEGER | not null |

Индексы: `ix_project_images_project_id` (project_id)

## `projects`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `slug` | VARCHAR(200) | unique, not null |
| `title` | VARCHAR(255) | not null |
| `short_description` | TEXT |  |
| `body` | TEXT |  |
| `cover` | JSONB |  |
| `year` | INTEGER |  |
| `customer_name` | VARCHAR(255) |  |
| `location` | VARCHAR(255) |  |
| `is_published` | BOOLEAN | not null |
| `sort` | INTEGER | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `publications`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `slug` | VARCHAR(200) | unique, not null |
| `title` | VARCHAR(255) | not null |
| `short_description` | TEXT |  |
| `body` | TEXT |  |
| `cover` | JSONB |  |
| `published_at` | DATETIME | index |
| `is_published` | BOOLEAN | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

Индексы: `ix_publications_published_at` (published_at)

## `redirects`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `old_path` | VARCHAR(500) | unique, not null |
| `new_path` | VARCHAR(500) | not null |
| `status_code` | INTEGER | not null |
| `is_active` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `services`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `slug` | VARCHAR(200) | unique, not null |
| `title` | VARCHAR(255) | not null |
| `short_description` | TEXT |  |
| `body` | TEXT |  |
| `cover` | JSONB |  |
| `icon` | VARCHAR(100) |  |
| `is_published` | BOOLEAN | not null |
| `sort` | INTEGER | not null |
| `meta_title` | VARCHAR(255) |  |
| `meta_description` | TEXT |  |
| `og_image` | JSONB |  |
| `noindex` | BOOLEAN | not null |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `sessions`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | CHAR(32) | PK |
| `token_hash` | VARCHAR(64) | unique, not null |
| `user_id` | INTEGER | FK → users.id (CASCADE), index, not null |
| `created_at` | DATETIME | not null |
| `expires_at` | DATETIME | not null |
| `ip` | VARCHAR(64) |  |
| `user_agent` | VARCHAR(300) |  |

Индексы: `ix_sessions_user_id` (user_id)

## `site_settings`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `company_name` | VARCHAR(255) | not null |
| `phone` | VARCHAR(64) |  |
| `email` | VARCHAR(255) |  |
| `address` | TEXT |  |
| `working_hours` | VARCHAR(255) |  |
| `map_embed` | TEXT |  |
| `hero_title` | VARCHAR(255) |  |
| `hero_subtitle` | TEXT |  |
| `hero_image` | JSONB |  |
| `about_short` | TEXT |  |
| `stats` | JSONB |  |
| `footer_text` | TEXT |  |
| `default_meta_title` | VARCHAR(255) |  |
| `default_meta_description` | TEXT |  |

## `tariffs`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `equipment_id` | INTEGER | FK → equipment.id (CASCADE), unique, not null |
| `price_per_shift` | NUMERIC(12, 2) |  |
| `price_per_day` | NUMERIC(12, 2) |  |
| `shift_hours` | INTEGER | not null |
| `min_units` | INTEGER | not null |
| `note` | TEXT |  |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

## `users`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `email` | VARCHAR(255) | unique, not null |
| `password_hash` | VARCHAR(255) | not null |
| `first_name` | VARCHAR(100) | not null |
| `last_name` | VARCHAR(100) | not null |
| `patronymic` | VARCHAR(100) |  |
| `phone` | VARCHAR(32) |  |
| `position` | VARCHAR(150) |  |
| `role` | VARCHAR(20) | not null |
| `organization_id` | INTEGER | FK → organizations.id (SET NULL), index |
| `is_active` | BOOLEAN | not null |
| `email_confirmed_at` | DATETIME |  |
| `blocked_at` | DATETIME |  |
| `blocked_reason` | TEXT |  |
| `last_login_at` | DATETIME |  |
| `created_at` | DATETIME | not null |
| `updated_at` | DATETIME | not null |

Индексы: `ix_users_organization_id` (organization_id)

## `webhook_deliveries`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `received_at` | DATETIME | not null |
| `headers` | JSONB |  |
| `body` | JSONB |  |
| `signature_valid` | BOOLEAN |  |

## `webhook_endpoints`

| Колонка | Тип | Ограничения |
|---|---|---|
| `id` | INTEGER | PK |
| `name` | VARCHAR(100) | not null |
| `url` | VARCHAR(500) | not null |
| `secret` | VARCHAR(255) | not null |
| `is_active` | BOOLEAN | not null |
| `events` | JSONB |  |
| `created_at` | DATETIME | not null |

Дополнительно: `ix_equipment_search_trgm` — GIN pg_trgm по `name || ' ' || model` для поиска; `ix_equipment_category_published`, `ix_inquiries_org_created`.

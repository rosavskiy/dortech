# Резервное копирование и восстановление

## Что и когда

- Ежедневно 03:00 (`/etc/cron.d/dortech-backup`): `deploy/backup.sh prod` → `backups/prod-ГГГГММДД-ЧЧММ.dump` (pg_dump, формат custom), `.sha256`, `.counts.json` (число строк в ключевых таблицах).
- По воскресеньям дополнительно `prod-media-*.tar.gz` (каталоги `media/` и `private/`).
- Ретенция: 14 дней для дампов, 8 недель для архивов media (`BACKUP_RETENTION_DAYS`).
- Рекомендуется копировать `backups/` во внешнее хранилище Заказчика (например, `rclone sync /srv/dortech/prod/backups remote:dortech-backups` в том же cron).

## Восстановление

```bash
# 1. выбрать дамп и проверить контрольную сумму
ls -la /srv/dortech/prod/backups/
# 2. восстановить (останавливает приложение, пересоздаёт БД, применяет миграции, сверяет counts, запускает)
/srv/dortech/prod/src/deploy/restore.sh prod /srv/dortech/prod/backups/prod-20261113-0300.dump 2>&1 | tee restore-$(date +%F).log
# 3. при необходимости вернуть файлы
tar -xzf /srv/dortech/prod/backups/prod-media-20261109-0300.tar.gz -C /srv/dortech/prod/
# 4. проверить вход клиентом и менеджером, открыть несколько заявок
```

Восстановление на другой сервер: выполнить разделы 2 из `INSTALL.md`, скопировать дамп и `media`, запустить `restore.sh`.

## Учебное восстановление (критерий приёмки «Резервная копия»)

Выполняется на тестовой среде с демо-данными: `backup.sh test` → `restore.sh test <dump>`; лог сохраняется в `docs/protocols/restore-drill-<дата>.log`, протокол — `docs/protocols/restore-drill-<дата>.md` (дата, файл, sha256, размер, версия кода, counts до/после, результат входа).

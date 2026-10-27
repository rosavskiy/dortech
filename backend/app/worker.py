"""Воркер очереди исходящих сообщений. Запуск: python -m app.worker"""

import asyncio
import logging

from app.core.logging import setup_logging

log = logging.getLogger("worker")


async def main() -> None:
    setup_logging()
    from app.services.delivery import process_outbox

    log.info("worker started")
    while True:
        try:
            n = await process_outbox()
            if n:
                log.info("processed %d messages", n)
        except Exception:
            log.exception("outbox cycle failed")
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())

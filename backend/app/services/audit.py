from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


def log_action(
    session: AsyncSession,
    *,
    actor: User | None,
    action: str,
    target: object,
    changes: dict | None = None,
    ip: str | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            actor_repr=str(actor) if actor else "система",
            action=action,
            target_type=type(target).__name__,
            target_id=str(getattr(target, "id", "")),
            object_repr=str(target)[:255],
            changes=changes,
            ip=ip,
        )
    )

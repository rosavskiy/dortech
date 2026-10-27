import pytest
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import OutboundMessage, User
from tests.conftest import PASSWORD, csrf, login

pytestmark = pytest.mark.usefixtures("seed")


async def _last_link(template: str) -> str:
    async with SessionLocal() as s:
        msgs = (await s.execute(select(OutboundMessage).order_by(OutboundMessage.id.desc()))).scalars().all()
        m = next(m for m in msgs if m.payload.get("template") == template)
        return m.payload["context"]["link"]


async def test_register_confirm_login(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "New@Example.com",
            "password": "Qwerty123",
            "first_name": "Н",
            "last_name": "К",
            "company_name": "ООО «Н»",
            "inn": "7700000000",
            "consent": True,
        },
    )
    assert r.status_code == 201
    assert (
        await client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": "Qwerty123"})
    ).status_code == 403
    token = (await _last_link("confirm_email")).split("token=")[1]
    r = await client.post("/api/v1/auth/confirm-email", json={"token": token})
    assert r.status_code == 200 and r.json()["organization"]["name"] == "ООО «Н»" and r.json()["role"] == "client"
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    assert (
        await client.post("/api/v1/auth/confirm-email", json={"token": token})
    ).status_code == 400  # повторно нельзя
    assert (
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "Qwerty123",
                "first_name": "Н",
                "last_name": "К",
                "company_name": "ООО «X»",
                "consent": True,
            },
        )
    ).status_code == 409


async def test_weak_password_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "w@example.com",
            "password": "12345678",
            "first_name": "Н",
            "last_name": "К",
            "company_name": "ООО «X»",
            "consent": True,
        },
    )
    assert r.status_code == 400, r.text


async def test_login_errors(client):
    assert (
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong"})
    ).status_code == 400
    assert (
        await client.post("/api/v1/auth/login", json={"email": "u@example.com", "password": PASSWORD})
    ).status_code == 403
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_logout_and_csrf(client):
    token = await login(client, "a@example.com")
    assert (await client.post("/api/v1/auth/logout")).status_code == 403  # без CSRF
    assert (await client.post("/api/v1/auth/logout", headers=csrf(token))).status_code == 200
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_password_reset_flow(client):
    assert (await client.post("/api/v1/auth/password-reset", json={"email": "nobody@example.com"})).status_code == 200
    assert (await client.post("/api/v1/auth/password-reset", json={"email": "a@example.com"})).status_code == 200
    token = (await _last_link("password_reset")).split("token=")[1]
    assert (
        await client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "NewPass123"})
    ).status_code == 200
    assert (
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    ).status_code == 400
    assert (
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "NewPass123"})
    ).status_code == 200


async def test_blocked_user_session_terminated(client, seed):
    from datetime import UTC, datetime

    await login(client, "a@example.com")
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    async with SessionLocal() as s:
        u = await s.get(User, seed["users"]["a"])
        u.blocked_at = datetime.now(UTC)
        await s.commit()
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (
        await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    ).status_code == 403

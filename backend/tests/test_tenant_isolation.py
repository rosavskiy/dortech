"""Критерий ТЗ 6 «Разделение доступа»: клиент А не получает данные, файлы и заявки клиента Б
ни через интерфейс, ни через прямые запросы. Список клиентских маршрутов проверяется на полноту."""

import io

import pytest
from httpx import AsyncClient

from app.main import app
from tests.conftest import create_inquiry, csrf, login

pytestmark = pytest.mark.usefixtures("seed")

PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

# Все клиентские маршруты с объектом в пути: (метод, шаблон, тело). Новый маршрут обязан попасть сюда — см. test_all_account_routes_covered.
OBJECT_ROUTES = [
    ("GET", "/api/v1/account/inquiries/{id}", None),
    ("POST", "/api/v1/account/inquiries/{id}/comments", {"text": "чужой комментарий"}),
    ("POST", "/api/v1/account/inquiries/{id}/files", "file"),
]


@pytest.fixture
async def two_clients(client: AsyncClient, seed):
    """Клиент Б создаёт заявку с файлом; возвращает её id, id файла и свежий клиент, вошедший как А."""
    tok_b = await login(client, "b@example.com")
    inq_b = await create_inquiry(client, seed["equipment"]["ex-komatsu-pc200"], token=tok_b, via_account=True)
    r = await client.post(
        f"/api/v1/account/inquiries/{inq_b['public_id']}/files",
        headers=csrf(tok_b),
        files={"file": ("doc.png", io.BytesIO(PNG), "image/png")},
    )
    assert r.status_code == 201, r.text
    file_b = r.json()["attachments"][0]["public_id"]
    await client.post("/api/v1/auth/logout", headers=csrf(tok_b))
    tok_a = await login(client, "a@example.com")
    inq_a = await create_inquiry(client, seed["equipment"]["roller-jcb-vmt"], token=tok_a, via_account=True)
    return {"inq_b": inq_b["public_id"], "file_b": file_b, "inq_a": inq_a["public_id"], "tok_a": tok_a}


@pytest.mark.parametrize("method,path,body", OBJECT_ROUTES)
async def test_client_a_cannot_touch_client_b_objects(client, two_clients, method, path, body):
    url = path.format(id=two_clients["inq_b"])
    kwargs = {"headers": csrf(two_clients["tok_a"])}
    if body == "file":
        kwargs["files"] = {"file": ("x.png", io.BytesIO(PNG), "image/png")}
    elif body:
        kwargs["json"] = body
    r = await client.request(method, url, **kwargs)
    assert r.status_code == 404, f"{method} {url} -> {r.status_code}"


async def test_lists_do_not_leak(client, two_clients):
    ids = {i["public_id"] for i in (await client.get("/api/v1/account/inquiries")).json()["items"]}
    assert ids == {two_clients["inq_a"]}


async def test_file_of_b_hidden_from_a_but_visible_to_staff(client, two_clients):
    assert (await client.get(f"/api/v1/files/{two_clients['file_b']}/download")).status_code == 404
    await client.post("/api/v1/auth/logout", headers=csrf(two_clients["tok_a"]))
    assert (await client.get(f"/api/v1/files/{two_clients['file_b']}/download")).status_code == 401
    await login(client, "m@example.com")
    assert (await client.get(f"/api/v1/files/{two_clients['file_b']}/download")).status_code == 200


async def test_client_cannot_use_manager_api(client, two_clients):
    for path in (
        "/api/v1/manager/inquiries",
        f"/api/v1/manager/inquiries/{two_clients['inq_b']}",
        "/api/v1/manager/organizations",
        "/api/v1/manager/inquiries/export.csv",
    ):
        assert (await client.get(path)).status_code == 403, path
    r = await client.post(
        f"/api/v1/manager/inquiries/{two_clients['inq_b']}/status",
        json={"status": "agreed"},
        headers=csrf(two_clients["tok_a"]),
    )
    assert r.status_code == 403


async def test_anonymous_gets_401(client, two_clients):
    await client.post("/api/v1/auth/logout", headers=csrf(two_clients["tok_a"]))
    for path in (
        "/api/v1/account/inquiries",
        f"/api/v1/account/inquiries/{two_clients['inq_a']}",
        "/api/v1/account/profile",
        "/api/v1/manager/inquiries",
    ):
        assert (await client.get(path)).status_code == 401, path


def test_all_account_routes_covered():
    """Любой клиентский маршрут с параметром в пути должен быть в OBJECT_ROUTES."""
    covered = {(m, p) for m, p, _ in OBJECT_ROUTES}
    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/v1/account/") and "{" in path:
            for method in route.methods - {"HEAD", "OPTIONS"}:
                key = (method, path.replace("{public_id}", "{id}"))
                assert key in covered, f"маршрут {method} {path} не покрыт тестом изоляции"

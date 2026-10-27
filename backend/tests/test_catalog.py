import pytest

pytestmark = pytest.mark.usefixtures("seed")


async def test_list_published_only(client):
    r = await client.get("/api/v1/catalog/equipment")
    assert r.status_code == 200
    slugs = {i["slug"] for i in r.json()["items"]}
    assert "ex-hidden" not in slugs and len(slugs) == 5


async def test_search_by_name_and_model(client):
    assert {i["slug"] for i in (await client.get("/api/v1/catalog/equipment?q=komatsu")).json()["items"]} == {
        "ex-komatsu-pc200",
        "ex-komatsu-pw160",
    }
    assert {i["slug"] for i in (await client.get("/api/v1/catalog/equipment?q=JS220")).json()["items"]} == {
        "ex-jcb-js220"
    }
    assert (await client.get("/api/v1/catalog/equipment?q=несуществующее")).json()["total"] == 0


async def test_filters(client):
    get = lambda qs: {i["slug"] for i in client_get.json()["items"]}  # noqa: E731
    client_get = await client.get("/api/v1/catalog/equipment?category=katki")
    assert get("") == {"roller-jcb-vmt"}
    client_get = await client.get("/api/v1/catalog/equipment?manufacturer=jcb&status=available")
    assert get("") == {"ex-jcb-3cx", "roller-jcb-vmt"}
    client_get = await client.get("/api/v1/catalog/equipment?attr_drive=Гусеничная")
    assert get("") == {"ex-komatsu-pc200", "ex-jcb-js220"}
    client_get = await client.get("/api/v1/catalog/equipment?attr_weight_min=16&attr_weight_max=21")
    assert get("") == {"ex-komatsu-pc200", "ex-komatsu-pw160"}
    client_get = await client.get("/api/v1/catalog/equipment?attr_with_operator=true&category=ekskavatory")
    assert get("") == {"ex-komatsu-pc200", "ex-jcb-js220", "ex-jcb-3cx"}
    client_get = await client.get("/api/v1/catalog/equipment?manufacturer=komatsu&attr_drive=Колёсная")
    assert get("") == {"ex-komatsu-pw160"}


async def test_sorting_and_pagination(client):
    r = await client.get("/api/v1/catalog/equipment?ordering=price&page_size=2")
    d = r.json()
    assert (
        d["pages"] == 3 and d["page"] == 1 and [i["slug"] for i in d["items"]] == ["roller-jcb-vmt", "ex-komatsu-pw160"]
    )
    r = await client.get("/api/v1/catalog/equipment?ordering=-price&page_size=2&page=2")
    assert [i["slug"] for i in r.json()["items"]] == ["ex-komatsu-pw160", "roller-jcb-vmt"], [
        (i["slug"], i["tariff"] and i["tariff"]["price_per_shift"]) for i in r.json()["items"]
    ]


async def test_garbage_params_do_not_crash(client):
    for qs in (
        "page=abc",
        "page=-5",
        "page_size=99999",
        "attr_weight_min=x",
        "ordering=drop+table",
        "q=" + "й" * 500,
        "manufacturer=,,,",
        "attr_unknown=1",
    ):
        r = await client.get(f"/api/v1/catalog/equipment?{qs}")
        assert r.status_code == 200, qs
    assert (await client.get("/api/v1/catalog/equipment?page=999")).json()["page"] == 1


async def test_detail_and_hidden_price(client):
    r = await client.get("/api/v1/catalog/equipment/ex-jcb-3cx")
    assert r.status_code == 200
    assert r.json()["price_hidden"] is True and r.json()["tariff"] is None
    assert (await client.get("/api/v1/catalog/equipment/ex-hidden")).status_code == 404
    assert (await client.get("/api/v1/catalog/equipment/nope")).status_code == 404


async def test_facets(client):
    f = (await client.get("/api/v1/catalog/facets?category=ekskavatory")).json()
    assert {m["value"]: m["count"] for m in f["manufacturers"]} == {"komatsu": 2, "jcb": 2}
    codes = {a["code"]: a for a in f["attributes"]}
    assert set(codes) == {"weight", "drive", "with_operator"}
    assert {o["value"]: o["count"] for o in codes["drive"]["options"]} == {"Гусеничная": 2, "Колёсная": 2}
    assert float(codes["weight"]["min"]) == 8 and float(codes["weight"]["max"]) == 22


async def test_compare_limits(client, seed):
    ids = list(seed["equipment"].values())
    assert (await client.get("/api/v1/catalog/compare?ids=" + ",".join(map(str, ids[:5])))).status_code == 400
    r = await client.get("/api/v1/catalog/compare?ids=" + ",".join(map(str, ids[:4])))
    assert r.status_code == 200 and len(r.json()["items"]) == 4
    assert "Масса" in [row["name"] for row in r.json()["rows"]]
    assert (await client.get("/api/v1/catalog/compare?ids=abc,,1")).status_code == 200

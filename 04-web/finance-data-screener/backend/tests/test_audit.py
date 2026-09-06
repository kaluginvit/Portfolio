from httpx import AsyncClient


async def test_list_audit_returns_200(client: AsyncClient):
    resp = await client.get("/audit")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_audit_logs_api_calls(client: AsyncClient):
    # Делаем несколько вызовов — middleware должна залогировать их
    await client.post("/datasets", json={"name": "Audit Test", "query": "q"})
    await client.get("/datasets")

    resp = await client.get("/audit")
    assert resp.status_code == 200
    runs = resp.json()
    # Два вызова выше должны быть залогированы (GET /health и /docs пропускаются)
    assert len(runs) >= 2
    endpoints = [r["endpoint"] for r in runs]
    assert "/datasets" in endpoints


async def test_audit_run_has_required_fields(client: AsyncClient):
    await client.post("/datasets", json={"name": "Field Test", "query": "test"})

    resp = await client.get("/audit")
    runs = resp.json()
    assert len(runs) >= 1

    run = runs[0]
    assert "id" in run
    assert "endpoint" in run
    assert "method" in run
    assert "status_code" in run
    assert "duration_ms" in run
    assert "created_at" in run
    assert "error" in run


async def test_audit_records_correct_status_codes(client: AsyncClient):
    # Успешный запрос → 201
    await client.post("/datasets", json={"name": "StatusTest", "query": "q"})
    # Невалидный → 422
    await client.post("/datasets", json={"name": "only name"})

    resp = await client.get("/audit")
    runs = resp.json()
    status_codes = {r["status_code"] for r in runs}
    assert 201 in status_codes
    assert 422 in status_codes

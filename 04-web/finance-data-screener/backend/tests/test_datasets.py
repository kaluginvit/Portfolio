import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AgentRun


# ---------------------------------------------------------------------------
# POST /datasets
# ---------------------------------------------------------------------------

async def test_create_dataset_returns_201(client: AsyncClient):
    resp = await client.post("/datasets", json={"name": "Test DS", "query": "test query"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test DS"
    assert data["query"] == "test query"
    assert data["records_count"] == 0
    assert data["source"] is None
    assert "id" in data
    assert "created_at" in data


async def test_create_dataset_missing_name_returns_422(client: AsyncClient):
    resp = await client.post("/datasets", json={"query": "only query"})
    assert resp.status_code == 422


async def test_create_dataset_missing_query_returns_422(client: AsyncClient):
    resp = await client.post("/datasets", json={"name": "only name"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /datasets
# ---------------------------------------------------------------------------

async def test_list_datasets_empty(client: AsyncClient):
    resp = await client.get("/datasets")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_datasets_returns_all_created(client: AsyncClient):
    await client.post("/datasets", json={"name": "DS1", "query": "q1"})
    await client.post("/datasets", json={"name": "DS2", "query": "q2"})

    resp = await client.get("/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {d["name"] for d in data}
    assert names == {"DS1", "DS2"}


# ---------------------------------------------------------------------------
# GET /datasets/{id}
# ---------------------------------------------------------------------------

async def test_get_dataset_returns_correct_item(client: AsyncClient):
    create_resp = await client.post("/datasets", json={"name": "MyDS", "query": "myq"})
    dataset_id = create_resp.json()["id"]

    resp = await client.get(f"/datasets/{dataset_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == dataset_id
    assert data["name"] == "MyDS"
    assert data["records_count"] == 0


async def test_get_dataset_not_found_returns_404(client: AsyncClient):
    resp = await client.get(f"/datasets/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /datasets/{id}/collect
# ---------------------------------------------------------------------------

async def _make_agent_run(
    db: AsyncSession,
    *,
    source: str = "cbr",
    needs_review: bool = False,
    review_reason: str | None = None,
) -> uuid.UUID:
    run_id = uuid.uuid4()
    db.add(AgentRun(
        id=run_id,
        query="test query",
        source=source,
        api_url="https://www.cbr-xml-daily.ru/daily_json.js",
        fields_to_keep=["CharCode", "Value"],
        filters={},
        needs_review=needs_review,
        review_reason=review_reason,
        confidence="high",
        plan_steps=["Fetch data"],
    ))
    await db.commit()
    return run_id


async def test_collect_saves_records(client: AsyncClient, db: AsyncSession):
    create_resp = await client.post("/datasets", json={"name": "Collect DS", "query": "cbr"})
    dataset_id = create_resp.json()["id"]
    run_id = await _make_agent_run(db)

    mock_collector = AsyncMock()
    mock_collector.collect = AsyncMock(return_value=[
        {"CharCode": "USD", "Value": 90.5},
        {"CharCode": "EUR", "Value": 98.2},
    ])

    with patch("app.api.datasets.CollectorFactory.get", return_value=mock_collector):
        resp = await client.post(
            f"/datasets/{dataset_id}/collect",
            json={"agent_run_id": str(run_id)},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["records_saved"] == 2
    assert data["source"] == "cbr"
    assert data["dataset_id"] == dataset_id


async def test_collect_dataset_not_found_returns_404(client: AsyncClient, db: AsyncSession):
    run_id = await _make_agent_run(db)
    resp = await client.post(
        f"/datasets/{uuid.uuid4()}/collect",
        json={"agent_run_id": str(run_id)},
    )
    assert resp.status_code == 404


async def test_collect_agent_run_not_found_returns_404(client: AsyncClient):
    create_resp = await client.post("/datasets", json={"name": "DS", "query": "q"})
    dataset_id = create_resp.json()["id"]

    resp = await client.post(
        f"/datasets/{dataset_id}/collect",
        json={"agent_run_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404


async def test_collect_needs_review_blocked_returns_422(client: AsyncClient, db: AsyncSession):
    create_resp = await client.post("/datasets", json={"name": "Review DS", "query": "q"})
    dataset_id = create_resp.json()["id"]
    run_id = await _make_agent_run(db, needs_review=True, review_reason="Query is ambiguous")

    resp = await client.post(
        f"/datasets/{dataset_id}/collect",
        json={"agent_run_id": str(run_id)},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /datasets/{id}/records
# ---------------------------------------------------------------------------

async def test_get_records_empty(client: AsyncClient):
    create_resp = await client.post("/datasets", json={"name": "DS", "query": "q"})
    dataset_id = create_resp.json()["id"]

    resp = await client.get(f"/datasets/{dataset_id}/records")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_records_after_collect(client: AsyncClient, db: AsyncSession):
    create_resp = await client.post("/datasets", json={"name": "DS2", "query": "q"})
    dataset_id = create_resp.json()["id"]
    run_id = await _make_agent_run(db)

    mock_collector = AsyncMock()
    mock_collector.collect = AsyncMock(return_value=[{"CharCode": "USD", "Value": 90.5}])

    with patch("app.api.datasets.CollectorFactory.get", return_value=mock_collector):
        await client.post(
            f"/datasets/{dataset_id}/collect",
            json={"agent_run_id": str(run_id)},
        )

    resp = await client.get(f"/datasets/{dataset_id}/records")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 1
    assert records[0]["source"] == "cbr"
    assert records[0]["data"]["CharCode"] == "USD"

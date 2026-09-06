import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import AgentRun, Dataset, Record


async def _make_dataset_with_records(db: AsyncSession, n: int = 3) -> str:
    ds_id = uuid.uuid4()
    db.add(Dataset(id=ds_id, name="Test DS", query="тест", source="cbr"))
    for i in range(n):
        db.add(Record(
            id=uuid.uuid4(),
            dataset_id=ds_id,
            source="cbr",
            data={"CharCode": f"USD{i}", "Value": 90.0 + i},
        ))
    await db.commit()
    return str(ds_id)


# ---------------------------------------------------------------------------
# POST /ai/query
# ---------------------------------------------------------------------------

async def test_query_returns_answer(client: AsyncClient, db: AsyncSession):
    dataset_id = await _make_dataset_with_records(db, n=3)

    mock_answer = AsyncMock()
    mock_answer.answer = "Средний курс: 91 руб."
    mock_answer.needs_review = False
    mock_answer.review_reason = None

    with patch("app.api.ai.query_dataset", return_value=mock_answer):
        resp = await client.post(
            "/ai/query",
            json={"dataset_id": dataset_id, "question": "какой средний курс?"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Средний курс: 91 руб."
    assert data["needs_review"] is False
    assert data["records_used"] == 3


async def test_query_needs_review_when_llm_unsure(client: AsyncClient, db: AsyncSession):
    dataset_id = await _make_dataset_with_records(db, n=2)

    mock_answer = AsyncMock()
    mock_answer.answer = "Данных недостаточно"
    mock_answer.needs_review = True
    mock_answer.review_reason = "Недостаточно данных для расчёта"

    with patch("app.api.ai.query_dataset", return_value=mock_answer):
        resp = await client.post(
            "/ai/query",
            json={"dataset_id": dataset_id, "question": "что-то непонятное?"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_review"] is True
    assert data["review_reason"] == "Недостаточно данных для расчёта"


async def test_query_dataset_not_found_returns_404(client: AsyncClient):
    resp = await client.post(
        "/ai/query",
        json={"dataset_id": str(uuid.uuid4()), "question": "вопрос?"},
    )
    assert resp.status_code == 404


async def test_query_empty_dataset_returns_404(client: AsyncClient, db: AsyncSession):
    ds_id = uuid.uuid4()
    db.add(Dataset(id=ds_id, name="Empty DS", query="пусто"))
    await db.commit()

    resp = await client.post(
        "/ai/query",
        json={"dataset_id": str(ds_id), "question": "вопрос?"},
    )
    assert resp.status_code == 404


async def test_query_short_question_returns_422(client: AsyncClient, db: AsyncSession):
    dataset_id = await _make_dataset_with_records(db, n=1)
    resp = await client.post(
        "/ai/query",
        json={"dataset_id": dataset_id, "question": "?"},
    )
    assert resp.status_code == 422


async def test_query_records_used_reflects_db_count(client: AsyncClient, db: AsyncSession):
    dataset_id = await _make_dataset_with_records(db, n=10)

    mock_answer = AsyncMock()
    mock_answer.answer = "10 записей"
    mock_answer.needs_review = False
    mock_answer.review_reason = None

    with patch("app.api.ai.query_dataset", return_value=mock_answer):
        resp = await client.post(
            "/ai/query",
            json={"dataset_id": dataset_id, "question": "сколько записей?"},
        )

    assert resp.status_code == 200
    assert resp.json()["records_used"] == 10

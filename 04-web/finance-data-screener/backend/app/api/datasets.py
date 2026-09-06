import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import AgentRun, Dataset, Record
from app.collectors.factory import CollectorFactory
from app.schemas.dataset import (
    CollectRequest,
    CollectResponse,
    DatasetCreate,
    DatasetRead,
    RecordRead,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetRead, status_code=201)
async def create_dataset(body: DatasetCreate, db: AsyncSession = Depends(get_db)):
    dataset = Dataset(id=uuid.uuid4(), name=body.name, query=body.query)
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return DatasetRead(
        id=str(dataset.id),
        name=dataset.name,
        query=dataset.query,
        source=dataset.source,
        created_at=dataset.created_at,
        records_count=0,
    )


@router.get("", response_model=list[DatasetRead])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Dataset.id,
            Dataset.name,
            Dataset.query,
            Dataset.source,
            Dataset.created_at,
            func.count(Record.id).label("records_count"),
        )
        .outerjoin(Record, Record.dataset_id == Dataset.id)
        .group_by(Dataset.id)
        .order_by(Dataset.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        DatasetRead(
            id=str(r.id),
            name=r.name,
            query=r.query,
            source=r.source,
            created_at=r.created_at,
            records_count=r.records_count,
        )
        for r in rows
    ]


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Dataset.id,
            Dataset.name,
            Dataset.query,
            Dataset.source,
            Dataset.created_at,
            func.count(Record.id).label("records_count"),
        )
        .outerjoin(Record, Record.dataset_id == Dataset.id)
        .where(Dataset.id == uuid.UUID(dataset_id))
        .group_by(Dataset.id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetRead(
        id=str(row.id),
        name=row.name,
        query=row.query,
        source=row.source,
        created_at=row.created_at,
        records_count=row.records_count,
    )


@router.post("/{dataset_id}/collect", response_model=CollectResponse)
async def collect_dataset(
    dataset_id: str, body: CollectRequest, db: AsyncSession = Depends(get_db)
):
    dataset = (
        await db.execute(select(Dataset).where(Dataset.id == uuid.UUID(dataset_id)))
    ).scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    agent_run = (
        await db.execute(
            select(AgentRun).where(AgentRun.id == uuid.UUID(body.agent_run_id))
        )
    ).scalar_one_or_none()
    if not agent_run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    if agent_run.needs_review:
        raise HTTPException(
            status_code=422,
            detail=f"Plan requires human review: {agent_run.review_reason}",
        )

    try:
        collector = CollectorFactory.get(agent_run.source)
        records_data = await collector.collect(
            api_url=agent_run.api_url,
            fields_to_keep=agent_run.fields_to_keep or [],
            filters=agent_run.filters or {},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Collection error: {e}")

    records = [
        Record(
            id=uuid.uuid4(),
            dataset_id=dataset.id,
            source=agent_run.source,
            data=row,
        )
        for row in records_data
    ]
    db.add_all(records)

    dataset.source = agent_run.source
    agent_run.dataset_id = dataset.id

    await db.commit()

    return CollectResponse(
        dataset_id=dataset_id,
        records_saved=len(records),
        source=agent_run.source,
    )


@router.get("/{dataset_id}/records", response_model=list[RecordRead])
async def get_records(
    dataset_id: str, limit: int = 500, db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(Record)
            .where(Record.dataset_id == uuid.UUID(dataset_id))
            .order_by(Record.collected_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        RecordRead(
            id=str(r.id),
            source=r.source,
            collected_at=r.collected_at,
            data=r.data,
        )
        for r in rows
    ]

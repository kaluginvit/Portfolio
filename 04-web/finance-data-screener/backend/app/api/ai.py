import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import AgentRun, Record
from app.schemas.ai import PlanRequest, PlanResponse, QueryRequest, QueryResponse
from app.services.llm import plan_collection, query_dataset

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/plan_and_collect", response_model=PlanResponse)
async def plan_and_collect(request: PlanRequest, db: AsyncSession = Depends(get_db)):
    try:
        plan = await plan_collection(request.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    run_id = uuid.uuid4()
    agent_run = AgentRun(
        id=run_id,
        query=request.query,
        source=plan.source,
        api_url=plan.api_url,
        fields_to_keep=plan.fields_to_keep,
        filters=plan.filters,
        confidence=plan.confidence,
        needs_review=plan.needs_review,
        plan_steps=plan.plan_steps,
        review_reason=plan.review_reason,
    )
    db.add(agent_run)
    await db.commit()

    return PlanResponse(agent_run_id=str(run_id), plan=plan)


@router.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Record)
            .where(Record.dataset_id == uuid.UUID(request.dataset_id))
            .order_by(Record.collected_at.desc())
            .limit(150)
        )
    ).scalars().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Dataset has no records")

    records_data = [r.data for r in rows]
    try:
        result = await query_dataset(request.question, records_data)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")

    return QueryResponse(
        answer=result.answer,
        records_used=len(records_data),
        needs_review=result.needs_review,
        review_reason=result.review_reason,
    )

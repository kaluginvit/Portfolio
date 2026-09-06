from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import AuditRun
from app.schemas.dataset import AuditRunRead

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditRunRead])
async def list_audit_runs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(AuditRun).order_by(AuditRun.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        AuditRunRead(
            id=str(r.id),
            endpoint=r.endpoint,
            method=r.method,
            status_code=r.status_code,
            duration_ms=r.duration_ms,
            created_at=r.created_at,
            request_body=r.request_body,
            response_summary=r.response_summary,
            error=r.error,
        )
        for r in rows
    ]

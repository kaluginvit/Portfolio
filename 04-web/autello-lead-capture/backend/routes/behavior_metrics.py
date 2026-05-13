from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.database import get_db
from models.behavior_metrics import BehaviorMetricsCRUD

router = APIRouter(prefix="/behavior-metrics", tags=["behavior-metrics"])


class BehaviorMetricsCreate(BaseModel):
    id: int
    time_on_page: Optional[int] = 0
    buttons_clicked: Optional[str] = None
    cursor_hover_areas: Optional[str] = None
    return_count: Optional[int] = 0


class BehaviorMetricsResponse(BehaviorMetricsCreate):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=BehaviorMetricsResponse)
def create_behavior_metrics(data: BehaviorMetricsCreate, db: Session = Depends(get_db)):
    return BehaviorMetricsCRUD.create(db, data.model_dump())


@router.get("/", response_model=List[BehaviorMetricsResponse])
def get_all_behavior_metrics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return BehaviorMetricsCRUD.get_all(db, skip=skip, limit=limit)


@router.get("/application/{application_id}", response_model=BehaviorMetricsResponse)
def get_behavior_metrics_by_application(application_id: int, db: Session = Depends(get_db)):
    obj = BehaviorMetricsCRUD.get_by_application_id(db, application_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return obj


@router.get("/{metrics_id}", response_model=BehaviorMetricsResponse)
def get_behavior_metrics(metrics_id: int, db: Session = Depends(get_db)):
    obj = BehaviorMetricsCRUD.get_by_id(db, metrics_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return obj


@router.put("/application/{application_id}", response_model=BehaviorMetricsResponse)
def update_behavior_metrics_by_application(application_id: int, data: BehaviorMetricsCreate, db: Session = Depends(get_db)):
    obj = BehaviorMetricsCRUD.update(db, application_id, data.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return obj


@router.put("/{metrics_id}", response_model=BehaviorMetricsResponse)
def update_behavior_metrics(metrics_id: int, data: BehaviorMetricsCreate, db: Session = Depends(get_db)):
    obj = BehaviorMetricsCRUD.update(db, metrics_id, data.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return obj


@router.delete("/{metrics_id}")
def delete_behavior_metrics(metrics_id: int, db: Session = Depends(get_db)):
    obj = BehaviorMetricsCRUD.delete(db, metrics_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Metrics not found")
    return {"message": "Deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from core.database import get_db
from models.admin_settings import AdminSettingsCRUD

router = APIRouter(prefix="/admin-settings", tags=["admin-settings"])


class AdminSettingsCreate(BaseModel):
    services: str
    budget_range: str


class AdminSettingsResponse(AdminSettingsCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=AdminSettingsResponse)
def create_admin_settings(data: AdminSettingsCreate, db: Session = Depends(get_db)):
    return AdminSettingsCRUD.create(db, data.model_dump())


@router.get("/", response_model=List[AdminSettingsResponse])
def get_all_admin_settings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return AdminSettingsCRUD.get_all(db, skip=skip, limit=limit)


@router.get("/latest", response_model=AdminSettingsResponse)
def get_latest_admin_settings(db: Session = Depends(get_db)):
    obj = AdminSettingsCRUD.get_latest(db)
    if not obj:
        raise HTTPException(status_code=404, detail="No admin settings found")
    return obj


@router.get("/{settings_id}", response_model=AdminSettingsResponse)
def get_admin_settings(settings_id: int, db: Session = Depends(get_db)):
    obj = AdminSettingsCRUD.get_by_id(db, settings_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Settings not found")
    return obj


@router.put("/{settings_id}", response_model=AdminSettingsResponse)
def update_admin_settings(settings_id: int, data: AdminSettingsCreate, db: Session = Depends(get_db)):
    obj = AdminSettingsCRUD.update(db, settings_id, data.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="Settings not found")
    return obj


@router.delete("/{settings_id}")
def delete_admin_settings(settings_id: int, db: Session = Depends(get_db)):
    obj = AdminSettingsCRUD.delete(db, settings_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"message": "Deleted"}

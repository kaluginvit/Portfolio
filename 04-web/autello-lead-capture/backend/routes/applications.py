from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from core.database import get_db
from models.application import ApplicationCRUD

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    business_info: Optional[str] = None
    budget: Optional[str] = None
    preferred_contact: Optional[str] = None
    comments: Optional[str] = None
    business_niche: Optional[str] = None
    company_size: Optional[str] = None
    task_volume: Optional[str] = None
    role: Optional[str] = None
    need_volume: Optional[str] = None
    deadline: Optional[str] = None
    task_type: Optional[str] = None
    interested_service: Optional[str] = None
    contact_time: Optional[str] = None


class ApplicationResponse(ApplicationCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=ApplicationResponse)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db)):
    return ApplicationCRUD.create(db, data.model_dump())


@router.get("/", response_model=List[ApplicationResponse])
def get_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ApplicationCRUD.get_all(db, skip=skip, limit=limit)


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    obj = ApplicationCRUD.get_by_id(db, application_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return obj


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, data: ApplicationCreate, db: Session = Depends(get_db)):
    obj = ApplicationCRUD.update(db, application_id, data.model_dump())
    if not obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return obj


@router.delete("/{application_id}")
def delete_application(application_id: int, db: Session = Depends(get_db)):
    obj = ApplicationCRUD.delete(db, application_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Deleted"}

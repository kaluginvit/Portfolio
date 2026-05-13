from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Session
from core.database import Base


class BehaviorMetrics(Base):
    """
    CREATE TABLE behavior_metrics (
        id INTEGER PRIMARY KEY REFERENCES applications(id),
        time_on_page INTEGER DEFAULT 0,
        buttons_clicked TEXT,
        cursor_hover_areas TEXT,
        return_count INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    __tablename__ = "behavior_metrics"

    id = Column(Integer, ForeignKey("applications.id"), primary_key=True)
    time_on_page = Column(Integer, default=0)
    buttons_clicked = Column(Text)
    cursor_hover_areas = Column(Text)
    return_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BehaviorMetricsCRUD:
    @staticmethod
    def create(db: Session, data: dict):
        obj = BehaviorMetrics(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(BehaviorMetrics).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, metrics_id: int):
        return db.query(BehaviorMetrics).filter(BehaviorMetrics.id == metrics_id).first()

    @staticmethod
    def get_by_application_id(db: Session, application_id: int):
        return db.query(BehaviorMetrics).filter(BehaviorMetrics.id == application_id).first()

    @staticmethod
    def update(db: Session, metrics_id: int, data: dict):
        obj = db.query(BehaviorMetrics).filter(BehaviorMetrics.id == metrics_id).first()
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            db.commit()
            db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, metrics_id: int):
        obj = db.query(BehaviorMetrics).filter(BehaviorMetrics.id == metrics_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

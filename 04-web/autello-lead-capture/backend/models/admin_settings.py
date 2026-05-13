from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import Session
from core.database import Base


class AdminSettings(Base):
    """
    CREATE TABLE admin_settings (
        id SERIAL PRIMARY KEY,
        services VARCHAR(255),
        budget_range VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    services = Column(String(255))
    budget_range = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdminSettingsCRUD:
    @staticmethod
    def create(db: Session, data: dict):
        obj = AdminSettings(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(AdminSettings).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, settings_id: int):
        return db.query(AdminSettings).filter(AdminSettings.id == settings_id).first()

    @staticmethod
    def get_latest(db: Session):
        return db.query(AdminSettings).order_by(AdminSettings.id.desc()).first()

    @staticmethod
    def update(db: Session, settings_id: int, data: dict):
        obj = db.query(AdminSettings).filter(AdminSettings.id == settings_id).first()
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            db.commit()
            db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, settings_id: int):
        obj = db.query(AdminSettings).filter(AdminSettings.id == settings_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

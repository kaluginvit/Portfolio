from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Session
from core.database import Base


class Application(Base):
    """
    CREATE TABLE applications (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        middle_name VARCHAR(255),
        business_info TEXT,
        budget VARCHAR(255),
        preferred_contact VARCHAR(255),
        comments TEXT,
        business_niche VARCHAR(255),
        company_size VARCHAR(255),
        task_volume VARCHAR(255),
        role VARCHAR(255),
        need_volume VARCHAR(255),
        deadline VARCHAR(255),
        task_type VARCHAR(255),
        interested_service VARCHAR(255),
        contact_time VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    middle_name = Column(String(255))
    business_info = Column(Text)
    budget = Column(String(255))
    preferred_contact = Column(String(255))
    comments = Column(Text)
    business_niche = Column(String(255))
    company_size = Column(String(255))
    task_volume = Column(String(255))
    role = Column(String(255))
    need_volume = Column(String(255))
    deadline = Column(String(255))
    task_type = Column(String(255))
    interested_service = Column(String(255))
    contact_time = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ApplicationCRUD:
    @staticmethod
    def create(db: Session, data: dict):
        obj = Application(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Application).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, application_id: int):
        return db.query(Application).filter(Application.id == application_id).first()

    @staticmethod
    def update(db: Session, application_id: int, data: dict):
        obj = db.query(Application).filter(Application.id == application_id).first()
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            db.commit()
            db.refresh(obj)
        return obj

    @staticmethod
    def delete(db: Session, application_id: int):
        obj = db.query(Application).filter(Application.id == application_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))  # moex | cbr | rbc
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    records: Mapped[list["Record"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class Record(Base):
    __tablename__ = "records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    dataset: Mapped["Dataset"] = relationship(back_populates="records")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))
    api_url: Mapped[str | None] = mapped_column(Text)
    fields_to_keep: Mapped[list[str] | None] = mapped_column(JSONB)
    filters: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confidence: Mapped[str | None] = mapped_column(String(20))  # high | medium | low
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_steps: Mapped[list[str] | None] = mapped_column(JSONB)
    review_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dataset: Mapped["Dataset | None"] = relationship(back_populates="agent_runs")


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    request_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    response_summary: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

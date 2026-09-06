from datetime import datetime
from typing import Any
from pydantic import BaseModel


class DatasetCreate(BaseModel):
    name: str
    query: str


class DatasetRead(BaseModel):
    id: str
    name: str
    query: str
    source: str | None
    created_at: datetime
    records_count: int


class CollectRequest(BaseModel):
    agent_run_id: str


class CollectResponse(BaseModel):
    dataset_id: str
    records_saved: int
    source: str


class RecordRead(BaseModel):
    id: str
    source: str
    collected_at: datetime
    data: dict[str, Any]


class AuditRunRead(BaseModel):
    id: str
    endpoint: str
    method: str
    status_code: int
    duration_ms: int
    created_at: datetime
    request_body: dict[str, Any] | None = None
    response_summary: str | None = None
    error: str | None

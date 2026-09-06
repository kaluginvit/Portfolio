from typing import Any, Literal
from pydantic import BaseModel, Field


class PlanRequest(BaseModel):
    query: str = Field(..., description="Запрос пользователя на русском языке")
    dataset_name: str | None = None


class CollectionPlan(BaseModel):
    source: Literal["moex", "cbr", "rbc"] = Field(description="Источник данных")
    api_url: str = Field(description="URL для сбора данных")
    fields_to_keep: list[str] = Field(description="Поля для сохранения")
    filters: dict[str, Any] = Field(default_factory=dict, description="Фильтры записей")
    confidence: Literal["high", "medium", "low"] = Field(description="Уверенность в плане")
    needs_review: bool = Field(description="true ТОЛЬКО если источника нет вообще (криптовалюта, иностранные акции, закрытые данные). false для любых запросов о валютах (cbr), акциях/облигациях/индексах (moex) и новостях (rbc) — даже если запрошена история или период.")
    plan_steps: list[str] = Field(description="Шаги выполнения плана")
    review_reason: str | None = Field(default=None, description="Причина необходимости проверки")


class PlanResponse(BaseModel):
    agent_run_id: str
    plan: CollectionPlan


class QueryRequest(BaseModel):
    dataset_id: str
    question: str = Field(..., min_length=3)


class QueryAnswer(BaseModel):
    answer: str = Field(description="Ответ на вопрос по данным на русском языке")
    needs_review: bool = Field(description="true если данных недостаточно для ответа")
    review_reason: str | None = Field(default=None, description="Причина если needs_review=true")


class QueryResponse(BaseModel):
    answer: str
    records_used: int
    needs_review: bool
    review_reason: str | None = None

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.datasets import router as datasets_router
from app.api.audit import router as audit_router
from app.middleware.audit import AuditMiddleware

app = FastAPI(
    title="AI Financial Screener",
    description="ИИ-скринер финансовых данных",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)

app.include_router(ai_router)
app.include_router(datasets_router)
app.include_router(audit_router)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}

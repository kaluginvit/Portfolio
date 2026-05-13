from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
from routes.applications import router as applications_router
from routes.behavior_metrics import router as behavior_metrics_router
from routes.admin_settings import router as admin_settings_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Autéllo Backend API",
    description="Приватный API для обработки заявок клиентов",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applications_router)
app.include_router(behavior_metrics_router)
app.include_router(admin_settings_router)

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from file_parser import parse_file
from claude_client import get_summary, chat as claude_chat

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("ФинАналитик API starting up")
    yield
    logger.info("ФинАналитик API shutting down")


app = FastAPI(title="ФинАналитик API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    table_data: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат .{ext}. Загрузите CSV или Excel файл.",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Файл пустой.")

    logger.info("Upload: filename=%s, size=%d bytes", file.filename, file_size)

    try:
        parsed = parse_file(file_bytes, file.filename)
    except ValueError as e:
        logger.error("Parse error for %s: %s", file.filename, e)
        raise HTTPException(status_code=400, detail=str(e))

    summary = get_summary(parsed["table_data"])

    return {
        "table_data": parsed["table_data"],
        "preview": parsed["preview"],
        "total_rows": parsed["total_rows"],
        "columns": parsed["columns"],
        "summary": summary,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    if not req.table_data:
        raise HTTPException(status_code=400, detail="Сначала загрузите файл с данными.")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым.")

    logger.info("Chat: message_len=%d, history_len=%d", len(req.message), len(req.history))

    try:
        response = claude_chat(req.message, req.history, req.table_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка при обращении к AI. Попробуйте позже.")

    return {"response": response}

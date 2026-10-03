import logging
import os
import threading

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import answer_question
from history_store import count_messages, init_db
from slack_history import SlackDirectory, backfill, record_event

load_dotenv("../../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PandaAgent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

directory = SlackDirectory(os.getenv("SLACK_BOT_TOKEN"))


class MessageRequest(BaseModel):
    text: str
    channel: str | None = None
    user: str | None = None


class AskRequest(BaseModel):
    text: str
    channel_id: str | None = None
    channel_type: str | None = None
    user_id: str | None = None
    user_name: str | None = None


class IngestRequest(BaseModel):
    channel_id: str
    ts: str
    text: str = ""
    user_id: str | None = None
    user_name: str | None = None
    channel_name: str | None = None
    channel_type: str | None = None
    thread_ts: str | None = None


class MessageResponse(BaseModel):
    response: str
    status: str


class HealthResponse(BaseModel):
    status: str
    service: str
    messages: int = 0


@app.on_event("startup")
def startup() -> None:
    init_db()
    threading.Thread(target=_startup_backfill, daemon=True).start()


def _startup_backfill() -> None:
    try:
        backfill(directory)
    except Exception as exc:
        logger.error("Startup backfill failed: %s", exc)


@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "ok",
        "service": "python-api",
        "messages": count_messages(),
    }


@app.post("/echo", response_model=MessageResponse)
async def echo(request: MessageRequest):
    return {
        "response": f"Echo: {request.text}",
        "status": "success",
    }


@app.post("/history/ingest")
async def ingest(request: IngestRequest):
    record_event(directory, request.model_dump())
    return {"status": "ok"}


@app.post("/ask", response_model=MessageResponse)
async def ask(request: AskRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Question text is required")
    logger.info("Ask from %s in %s: %s", request.user_id, request.channel_id, request.text)
    response = answer_question(request.text, request.user_id, request.user_name, request.channel_id)
    return {"response": response, "status": "success"}


@app.post("/ask-claude", response_model=MessageResponse)
async def ask_claude(request: MessageRequest):
    response = answer_question(request.text, request.user, None)
    return {"response": response, "status": "success"}


@app.post("/process-message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    return await ask(
        AskRequest(text=request.text, channel_id=request.channel, user_id=request.user)
    )


@app.get("/")
async def root():
    return {
        "name": "PandaAgent API",
        "version": "0.2.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "history_ingest": "/history/ingest",
            "echo": "/echo",
        },
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

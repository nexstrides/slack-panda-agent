import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import anthropic

load_dotenv("../../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PandaAgent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

claude_api_key = os.getenv("CLAUDE_API_KEY")
claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

if not claude_api_key:
    logger.warning("CLAUDE_API_KEY not set - Claude features will be unavailable")
    client = None
else:
    client = anthropic.Anthropic(api_key=claude_api_key)

class MessageRequest(BaseModel):
    text: str
    channel: str | None = None
    user: str | None = None

class MessageResponse(BaseModel):
    response: str
    status: str

class HealthResponse(BaseModel):
    status: str
    service: str

@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "ok",
        "service": "python-api"
    }

@app.post("/echo", response_model=MessageResponse)
async def echo(request: MessageRequest):
    logger.info(f"Echo request: {request.text}")
    return {
        "response": f"Echo: {request.text}",
        "status": "success"
    }

@app.post("/ask-claude", response_model=MessageResponse)
async def ask_claude(request: MessageRequest):
    if not client:
        raise HTTPException(status_code=503, detail="Claude API not configured")

    try:
        logger.info(f"Claude request: {request.text}")
        message = client.messages.create(
            model=claude_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": request.text}]
        )
        response_text = message.content[0].text

        return {
            "response": response_text,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling Claude API: {str(e)}")

@app.post("/process-message", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    try:
        logger.info(f"Processing message: {request.text} from {request.user}")
        response = f"Processed: {request.text}"
        return {
            "response": response,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/")
async def root():
    return {
        "name": "PandaAgent API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "echo": "/echo",
            "ask_claude": "/ask-claude",
            "process_message": "/process-message"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
from pathlib import Path

import uvicorn
from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .chat import answer_question

load_dotenv()

app = FastAPI()

# Single-user local demo: one shared conversation/cost total for the whole
# process, not per-visitor sessions — fine for running this yourself, not
# for multiple people using it at once.
_client = Anthropic(base_url=os.environ.get("API_ENDPOINT_BASE_URL"))
_model = os.environ.get("CLAUDE_MODEL")
_messages: list[dict] = []
_totals = {"usage_total": 0, "price_total": 0}

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text()


@app.post("/chat")
def chat(request: ChatRequest):
    answer, results = answer_question(_client, _model, _messages, request.question, _totals)
    return {
        "answer": answer,
        "sources": [{"path": r.path, "url": r.url} for r in results],
    }


def serve():
    uvicorn.run(app, host="127.0.0.1", port=8000)

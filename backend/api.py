from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from typing import  Literal
from chart_tools import create_chart_file, CHART_DIR

from rag_chain import ask_rag
from audio_tools import speak_text_to_audio_file
from chat_store import (
    create_chat_session,
    add_chat_message,
    get_chat_history,
    list_chat_sessions,
    clear_chat_session,
)


BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "generated_charts"
CHART_DIR.mkdir(exist_ok=True)
AUDIO_DIR = BASE_DIR / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)


app = FastAPI(title="Local RAG Chat API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/audio",
    StaticFiles(directory=str(AUDIO_DIR)),
    name="audio",
)

app.mount(
    "/charts",
    StaticFiles(directory=str(CHART_DIR)),
    name="charts",
)


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class SpeakRequest(BaseModel):
    text: str
    voice: str = "Samantha"
    rate: int = 180


class SpeakResponse(BaseModel):
    message: Optional[str] = None
    audio_url: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    error: Optional[str] = None


class ChartRequest(BaseModel):
    title: str = "Generated Chart"
    data: dict[str, float]
    chart_type: Literal["bar", "line", "pie"] = "bar"
    x_label: str = "Category"
    y_label: str = "Value"


class ChartResponse(BaseModel):
    message: str | None = None
    chart_url: str | None = None
    file_name: str | None = None
    chart_type: str | None = None
    error: str | None = None


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"


@app.get("/")
def health_check():
    return {"status": "RAG Chat API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id

    if not session_id:
        session = create_chat_session(title=request.question[:50])
        session_id = session["session_id"]

    answer = ask_rag(
        question=request.question,
        session_id=session_id,
    )

    add_chat_message(
        session_id=session_id,
        role="user",
        content=request.question,
    )

    add_chat_message(
        session_id=session_id,
        role="assistant",
        content=answer,
    )

    return ChatResponse(
        answer=answer,
        session_id=session_id,
    )


@app.post("/ask", response_model=ChatResponse)
def ask_question(request: ChatRequest):
    """
    Keep /ask for compatibility, but now it behaves like chat.
    """
    return chat(request)


@app.post("/sessions")
def create_session(request: CreateSessionRequest):
    return create_chat_session(title=request.title)


@app.get("/sessions")
def get_sessions():
    return list_chat_sessions(limit=20)


@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    return get_chat_history(session_id=session_id, limit=50)


@app.delete("/sessions/{session_id}/messages")
def clear_messages(session_id: str):
    return clear_chat_session(session_id=session_id)


@app.post("/speak", response_model=SpeakResponse)
def speak_answer(request: SpeakRequest):
    result = speak_text_to_audio_file(
        text=request.text,
        voice=request.voice,
        rate=request.rate,
    )

    if "error" in result:
        return SpeakResponse(error=result["error"])

    file_name = result["file_name"]

    return SpeakResponse(
        message=result.get("message"),
        audio_url=f"http://localhost:8000/audio/{file_name}",
        file_name=file_name,
        mime_type=result.get("mime_type"),
    )


@app.post("/chart", response_model=ChartResponse)
def generate_chart(request: ChartRequest):
    try:
        result = create_chart_file(
            title=request.title,
            data=request.data,
            chart_type=request.chart_type,
            x_label=request.x_label,
            y_label=request.y_label,
        )

        file_name = result["file_name"]

        return ChartResponse(
            message=result.get("message"),
            chart_url=f"http://localhost:8000/charts/{file_name}",
            file_name=file_name,
            chart_type=result.get("chart_type"),
        )

    except Exception as e:
        return ChartResponse(error=str(e))
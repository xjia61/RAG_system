from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from typing import  Literal
from chart_tools import create_chart_file, CHART_DIR
import shutil
import json 

from rag_pipline import add_document_to_vectorstore, retrieve_context
from rag_chain import ask_rag
from audio_tools import speak_text_to_audio_file
from chat_store import (
    create_chat_session,
    add_chat_message,
    get_chat_history,
    list_chat_sessions,
    clear_chat_session,
)
import uuid
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


#static folder
BASE_DIR = Path(__file__).resolve().parent

CHART_DIR = BASE_DIR / "generated_charts"
CHART_DIR.mkdir(exist_ok=True)

AUDIO_DIR = BASE_DIR / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)

UPLOAD_DIR =BASE_DIR/"uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

STATIC_DIR =BASE_DIR/"static"
STATIC_DIR.mkdir(exist_ok=True)

CHART_DIR = STATIC_DIR/"charts"
CHART_DIR.mkdir(exist_ok=True)




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

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name = "static"
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



@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())

    safe_filename = file.filename.replace(" ", "_")
    file_path = UPLOAD_DIR / f"{session_id}_{safe_filename}"

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    index_result = add_document_to_vectorstore(
        file_path=file_path,
        original_filename=file.filename,
    )

    return {
        "message": "Document uploaded and added to the existing vector database.",
        "session_id": session_id,
        "filename": file.filename,
        "index_result": index_result,
    }




from typing import Optional
from pydantic import BaseModel
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen3.5:2b")


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@app.post("/chat")
async def chat(payload: ChatRequest):
    session_id = payload.session_id or str(uuid.uuid4())

    docs, context_items = retrieve_context(payload.question, k=5)

    if not docs:
        return {
            "answer": "No indexed documents were found. Please upload a document first.",
            "session_id": session_id,
            "context": [],
        }

    context_text = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            for doc in docs
        ]
    )

    prompt = f"""
You are PathologyAI, an assistant for pathology reports and synthetic EHR-style documents.

Answer the user's question using only the retrieved context.
If the answer is not present in the context, say it is not mentioned in the provided document.

Retrieved context:
{context_text}

Question:
{payload.question}

Answer:
"""

    answer = llm.invoke(prompt)

    return {
        "answer": answer,
        "session_id": session_id,
        "context": context_items,
    }

"""

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

 """


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

"""
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
    
"""
class ChartRequest(BaseModel):
    title: str = "Generated Chart"
    chart_type: str = "bar"
    x_label: str = "Category"
    y_label: str = "Value"
    data: Dict[str, Any]


@app.post("/chart")
async def generate_chart(payload: ChartRequest, request: Request):
    """
    Generate a simple chart from JSON data.
    Frontend sends:
    {
      "title": "Generated Chart",
      "chart_type": "bar",
      "x_label": "Category",
      "y_label": "Value",
      "data": {
        "Melanoma": 12,
        "SCC": 8,
        "BCC": 15
      }
    }
    """

    labels = list(payload.data.keys())
    values = list(payload.data.values())

    try:
        values = [float(v) for v in values]
    except ValueError:
        return {"error": "All chart values must be numeric."}

    chart_id = str(uuid.uuid4())
    chart_filename = f"{chart_id}.png"
    chart_path = CHART_DIR / chart_filename

    plt.figure(figsize=(7, 4.5))

    if payload.chart_type == "bar":
        plt.bar(labels, values)
    elif payload.chart_type == "line":
        plt.plot(labels, values, marker="o")
    elif payload.chart_type == "pie":
        plt.pie(values, labels=labels, autopct="%1.1f%%")
    else:
        return {"error": "Unsupported chart type. Use bar, line, or pie."}

    if payload.chart_type != "pie":
        plt.xlabel(payload.x_label)
        plt.ylabel(payload.y_label)

    plt.title(payload.title)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close()

    chart_url = str(request.base_url).rstrip("/") + f"/static/charts/{chart_filename}"

    return {
        "chart_url": chart_url
    }

@app.post("/extract")
async def extract_structured_fields(payload: Dict[str, Any] = {}):
    query = """
    final diagnosis specimen type tumor site margin status lymph node metastasis biomarkers
    immunohistochemistry molecular pathology pathology report
    """

    docs, context_items = retrieve_context(query, k=8)

    if not docs:
        return {
            "extraction": {
                "diagnosis": "No indexed document found.",
                "specimen_type": "No indexed document found.",
                "tumor_site": "No indexed document found.",
                "margin_status": "No indexed document found.",
                "lymph_node_status": "No indexed document found.",
                "biomarkers": "No indexed document found.",
                "summary": "Please upload a document first.",
            },
            "context": [],
        }

    context_text = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            for doc in docs
        ]
    )

    prompt = f"""
You are extracting structured information from pathology reports.

Use only the provided context.

Return valid JSON only.
Do not add markdown.
Do not add explanation outside JSON.

Fields:
- diagnosis
- specimen_type
- tumor_site
- margin_status
- lymph_node_status
- biomarkers
- immunohistochemistry
- molecular_findings
- summary

If a field is not mentioned, use "Not mentioned".

Context:
{context_text}

JSON:
"""

    raw_output = llm.invoke(prompt)

    try:
        extraction = json.loads(raw_output)
    except json.JSONDecodeError:
        extraction = {
            "raw_extraction": raw_output,
            "note": "Model did not return valid JSON. Displaying raw extraction.",
        }

    return {
        "extraction": extraction,
        "context": context_items,
    }
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rag.chat import query_rag
from rag.populate_database import populate_database, ingest_document

# from rag.obsidian_writer import write_book_to_vault  # nuevo
import httpx
import json
import os
import shutil
import uuid
import subprocess

# Config
OPENCLAW_URL = "http://localhost:18789"
OPENCLAW_TOKEN = ()  # el token del openclaw.json
VAULT_PATH = "/home/rdlvg/Documentos/Obsidian Vault"
TELEGRAM_CHAT_ID = ""  # tu chat id


class ChatRequest(BaseModel):
    question: str
    scope: str = None  # "10_Libros", "20_DISENO", etc.


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def notify_telegram(message: str):
    """Notifica al usuario en Telegram via OpenClaw"""
    try:
        subprocess.run(
            [
                "openclaw",
                "message",
                "send",
                "--channel",
                "telegram",
                "--target",
                "7188574247",
                "--message",
                message,
            ]
        )
    except Exception as e:
        print(f"Error notificando AIRA: {e}")


async def run_ingest(file_path: str, original_name: str, job_id: str):
    """Pipeline completo en background"""
    try:
        notify_telegram(f"Procesando *{original_name}*... (job `{job_id}`)")

        # 1. Indexar en Chroma
        ingest_document(file_path)

        # 2. Generar notas en Obsidian
        # result = await write_book_to_vault(file_path, original_name, VAULT_PATH)

        notify_telegram(
            f"*{original_name}* lista!\n"
            # f"Capítulos: {result['chapters']}\n"
            # f" Examen: {result['exam_questions']} preguntas\n"
            # f"Guardado en: `{result['vault_path']}`\n"
            # f"Revisa borradores en `00_INBOX/Borradores_IA/`"
        )
    except Exception as e:
        notify_telegram(f"Error procesando {original_name}: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(request: ChatRequest):
    def generate():
        try:
            for item in query_rag(request.question, scope=request.scope):
                yield f"data: {json.dumps(item)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/populate")
async def populate(reset: bool = False):
    populate_database(reset=reset)
    return {"message": "Database populated successfully"}


@app.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)
):
    jobs = []
    for file in files:
        job_id = str(uuid.uuid4())[:8]
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"data/documents/{unique_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Responde inmediato, procesa en background
        background_tasks.add_task(run_ingest, file_path, file.filename, job_id)
        jobs.append({"file": file.filename, "job_id": job_id})

    return {"message": "Archivos recibidos, procesando en background", "jobs": jobs}

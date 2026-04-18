from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rag.chat import query_rag, retrieve_documents
from rag.obsidian_writer import write_book_to_vault
from rag.populate_database import populate_database, ingest_document
from dotenv import load_dotenv
import hashlib
import json
import os
import shutil
import uuid
import subprocess
import time

load_dotenv()

# Config
OPENCLAW_URL = os.getenv("OPENCLAW_URL")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN")
VAULT_PATH = os.getenv("VAULT_PATH")
VAULT_INDEX_PATH = "/app/chroma/vault_index.json"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "86400"))
_JOBS: dict[str, dict] = {}


def _job_set(job_id: str, **updates):
    now = int(time.time())
    job = _JOBS.get(job_id) or {}
    job.update({"job_id": job_id, "updated_at": now})
    if "created_at" not in job:
        job["created_at"] = now
    job.update(updates)
    _JOBS[job_id] = job


def _jobs_prune():
    now = int(time.time())
    expired = [
        job_id
        for job_id, job in _JOBS.items()
        if now - int(job.get("updated_at", now)) > JOB_TTL_SECONDS
    ]
    for job_id in expired:
        _JOBS.pop(job_id, None)


class ChatRequest(BaseModel):
    question: str
    scope: str = None


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_file_hash(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_vault_index():
    if os.path.exists(VAULT_INDEX_PATH):
        with open(VAULT_INDEX_PATH) as f:
            return json.load(f)
    return {}


def save_vault_index(index):
    with open(VAULT_INDEX_PATH, "w") as f:
        json.dump(index, f)


def notify_telegram(message: str):
    try:
        subprocess.run(
            [
                "docker",
                "exec",
                "aira-openclaw",
                "node",
                "dist/index.js",
                "message",
                "send",
                "--channel",
                "telegram",
                "--target",
                os.getenv("TELEGRAM_CHAT_ID"),
                "--message",
                message,
            ],
            timeout=15,
        )
    except Exception as e:
        print(f"Error notifying: {e}")


async def run_ingest(file_path: str, original_name: str, job_id: str):
    print(f"Iniciando ingesta: {original_name} ({job_id})")
    _job_set(
        job_id,
        status="processing",
        stage="starting",
        file=original_name,
    )
    try:
        # notify_telegram(f"Procesando *{original_name}*... (job `{job_id}`)")

        # Index
        print("Indexando en Chroma...")
        _job_set(job_id, stage="indexing_chroma")
        ingest_document(file_path)
        print(f"Chroma listo, generando notas en Obsidian...")

        # FIX generate notes on obsidian using tool
        _job_set(job_id, stage="writing_obsidian")
        result = await write_book_to_vault(file_path, original_name, VAULT_PATH)
        print(f"Obsidian listo: {result}")
        _job_set(job_id, status="done", stage="completed", result=result)

        # notify_telegram(
        #     f"*{original_name}* lista!\n"
        #     f"Capítulos: {result['chapters']}\n"
        #     f" Examen: {result['exam_questions']} preguntas\n"
        #     f"Guardado en: `{result['vault_path']}`\n"
        #     f"Revisa borradores en `00_INBOX/Borradores_IA/`"
        # )
    except Exception as e:
        print(f"Error en ingesta: {str(e)}")
        import traceback

        traceback.print_exc()
        _job_set(
            job_id,
            status="error",
            stage="failed",
            error_type=type(e).__name__,
            error=str(e),
        )
        notify_telegram(f"Error: {str(e)}")


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


@app.get("/retrieval-test")
async def retrieval_test(query: str, scope: str = None, top_k: int = 5):
    if not query.strip():
        raise HTTPException(status_code=400, detail="query is required")
    if top_k < 1 or top_k > 20:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 20")

    docs, sources = retrieve_documents(query, scope=scope, top_k=top_k)
    return {
        "query": query,
        "scope": scope,
        "top_k": top_k,
        "results_count": len(docs),
        "sources": sources,
    }


@app.post("/populate")
async def populate(reset: bool = False):
    populate_database(reset=reset)
    return {"message": "Database populated successfully"}


@app.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)
):
    _jobs_prune()
    print("Running upload process...")
    jobs = []
    for file in files:
        job_id = str(uuid.uuid4())[:8]
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"data/documents/{unique_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("Adding task to background process...")
        _job_set(
            job_id,
            status="queued",
            stage="queued",
            file=file.filename,
            file_path=file_path,
        )
        background_tasks.add_task(run_ingest, file_path, file.filename, job_id)
        jobs.append({"file": file.filename, "job_id": job_id})

    return {"message": "Archivos recibidos, procesando en background", "jobs": jobs}


@app.get("/jobs")
async def list_jobs(limit: int = 50):
    _jobs_prune()
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    jobs = sorted(_JOBS.values(), key=lambda j: j.get("created_at", 0), reverse=True)
    return {"jobs": jobs[:limit], "total": len(_JOBS)}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    _jobs_prune()
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/index-vault")
async def index_vault():
    import glob

    vault_path = os.getenv("VAULT_PATH", "/vault")
    md_files = glob.glob(f"{vault_path}/**/*.md", recursive=True)

    vault_index = load_vault_index()
    indexed = 0
    skipped = 0

    for md_file in md_files:
        current_hash = get_file_hash(md_file)
        if vault_index.get(md_file) == current_hash:
            skipped += 1
            continue
        try:
            ingest_document(md_file)
            vault_index[md_file] = current_hash
            indexed += 1
        except Exception as e:
            print(f"Error indexando {md_file}: {e}")

    save_vault_index(vault_index)
    return {"indexed": indexed, "skipped": skipped, "total": len(md_files)}

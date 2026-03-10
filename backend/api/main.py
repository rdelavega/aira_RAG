from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rag.chat import query_rag
from rag.populate_database import populate_database, ingest_document
import json
import os
import shutil
import uuid


class ChatRequest(BaseModel):
    question: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(request: ChatRequest):

    question = request.question

    def generate():
        try:
            for item in query_rag(question):
                yield f"data: {json.dumps(item)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/populate")
async def populate(reset: bool = False):
    populate_database(reset=reset)
    return {"message": "Database populated successfully"}


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        # Save file to data/documents/
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = f"data/documents/{unique_name}"
        print(f"Indexing file: {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)

        # Ingest the single document
        ingest_document(file_path)

    return {"message": f"Files uploaded and indexed: {uploaded_files}"}

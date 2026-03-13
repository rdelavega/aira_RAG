import argparse
import os
import shutil
from langchain_community.document_loaders import (
    PyPDFDirectoryLoader,
    PyPDFLoader,
    DirectoryLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from rag.get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"
DATA_PATH = "data"


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    populate_database(reset=args.reset)


def populate_database(reset=False):
    if reset:
        print("Clearing Database...")
        clear_database()

    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def ingest_document(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".md"):
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    documents = []
    # document_loader = PyPDFDirectoryLoader(DATA_PATH)
    # return document_loader.load()
    pdf_loader = PyPDFDirectoryLoader(DATA_PATH)
    documents.extend(pdf_loader.load())

    md_loader = DirectoryLoader(
        DATA_PATH, glob="**/*.md", loader_cls=UnstructuredMarkdownLoader
    )

    documents.extend(md_loader.load())
    return documents


def split_documents(documents):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)

    filtered_chunks = [c for c in chunks if len(c.page_content.strip()) > 100]

    return filtered_chunks


def add_to_chroma(chunks):
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("No new documents to add")


def calculate_chunk_ids(chunks):

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        chunk.metadata["id"] = chunk_id
        chunk.metadata["filename"] = os.path.basename(source)
        chunk.metadata["chunk_index"] = current_chunk_index

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto completo de un PDF como string"""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    return "\n\n".join([doc.page_content for doc in documents])


if __name__ == "__main__":
    main()

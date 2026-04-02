from langchain_ollama import OllamaEmbeddings
import os


def get_embedding_function():
    embeddings = OllamaEmbeddings(
        model="bge-m3",
        base_url=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"),
    )
    return embeddings

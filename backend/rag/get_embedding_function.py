import os
import httpx


class _OllamaEmbedder:
    """Calls Ollama /api/embed directly, bypassing langchain-ollama internals."""

    def __init__(self, host: str, model: str):
        self.url = f"{host.rstrip('/')}/api/embed"
        self.model = model

    def _embed(self, texts: list[str]) -> list[list[float]]:
        with httpx.Client(timeout=120) as client:
            resp = client.post(self.url, json={"model": self.model, "input": texts})
            resp.raise_for_status()
        return resp.json()["embeddings"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


def get_embedding_function():
    host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    return _OllamaEmbedder(host=host, model="bge-m3")

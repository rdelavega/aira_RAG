import os
import httpx


class _OllamaEmbedder:
    def __init__(self, host: str, model: str):
        self.url = f"{host.rstrip('/')}/api/embed"
        self.model = model

    def _embed_one(self, text: str) -> list[float]:
        with httpx.Client(timeout=120) as client:
            resp = client.post(self.url, json={"model": self.model, "input": text})
            resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings") or data.get("embedding")
        if isinstance(embeddings[0], list):
            return embeddings[0]
        return embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)


def get_embedding_function():
    host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    return _OllamaEmbedder(host=host, model="bge-m3")

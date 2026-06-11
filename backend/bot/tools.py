import os
import httpx
from pathlib import Path

RAG_URL = os.getenv("RAG_URL", "http://fastapi:8000")
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
VAULT_ROOT = Path(os.getenv("VAULT_PATH", "/vault"))

TOOL_DEFINITIONS = [
    {
        "name": "query_rag",
        "description": (
            "Consulta el sistema RAG para responder preguntas sobre libros, notas e "
            "investigaciones indexadas en el vault de Obsidian. Úsalo SIEMPRE antes de "
            "buscar en internet cuando la pregunta sea sobre contenido del usuario."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "La pregunta a responder usando el conocimiento indexado",
                },
                "scope": {
                    "type": "string",
                    "description": (
                        "Carpeta del vault para acotar la búsqueda. "
                        "Ejemplos: '10_Libros', '20_DISENO', '30_NEGOCIO'. Opcional."
                    ),
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "web_search",
        "description": "Busca información actual en internet. Usar solo cuando la información no está en las notas del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Términos de búsqueda"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "vault_list",
        "description": "Lista carpetas y archivos del vault de Obsidian.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Subcarpeta a listar (relativa al vault). Vacío para la raíz.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "vault_read",
        "description": "Lee el contenido de una nota específica del vault. Usar solo cuando el usuario pide ver literalmente una nota, no para responder preguntas de contenido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ruta relativa de la nota dentro del vault (ej: '10_Libros/MiLibro/Cap01.md')",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "vault_write",
        "description": "Crea o actualiza una nota en el vault de Obsidian.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ruta relativa dentro del vault (ej: '00_INBOX/nueva_nota.md')",
                },
                "content": {
                    "type": "string",
                    "description": "Contenido de la nota en formato Markdown con frontmatter YAML",
                },
            },
            "required": ["path", "content"],
        },
    },
]


def _safe_path(relative: str) -> Path | None:
    try:
        target = (VAULT_ROOT / relative).resolve()
        if not str(target).startswith(str(VAULT_ROOT.resolve())):
            return None
        return target
    except Exception:
        return None


async def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "query_rag":
            return await _query_rag(inputs["question"], inputs.get("scope"))
        if name == "web_search":
            return await _web_search(inputs["query"])
        if name == "vault_list":
            return _vault_list(inputs.get("path", ""))
        if name == "vault_read":
            return _vault_read(inputs["path"])
        if name == "vault_write":
            return _vault_write(inputs["path"], inputs["content"])
        return f"Tool desconocida: {name}"
    except Exception as e:
        return f"Error en {name}: {e}"


async def _query_rag(question: str, scope: str | None = None) -> str:
    payload = {"question": question}
    if scope:
        payload["scope"] = scope
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{RAG_URL}/query", json=payload)
        resp.raise_for_status()
    data = resp.json()
    answer = data.get("answer", "Sin respuesta del RAG.")
    sources = data.get("sources", [])
    if sources:
        filenames = ", ".join(s["filename"] for s in sources if s.get("filename"))
        return f"{answer}\n\n[Fuentes: {filenames}]"
    return answer


async def _web_search(query: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json", "categories": "general"},
        )
        resp.raise_for_status()
    results = resp.json().get("results", [])[:3]
    if not results:
        return "No se encontraron resultados."
    parts = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")[:300]
        url = r.get("url", "")
        parts.append(f"{title}\n{content}\n{url}")
    return "\n\n---\n\n".join(parts)


def _vault_list(path: str = "") -> str:
    target = VAULT_ROOT if not path else _safe_path(path)
    if target is None:
        return "Ruta inválida."
    if not target.exists():
        return f"No existe la ruta: {path}"
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = [("📁 " if e.is_dir() else "📄 ") + e.name for e in entries]
    return "\n".join(lines) if lines else "(vacío)"


def _vault_read(path: str) -> str:
    target = _safe_path(path)
    if target is None:
        return "Ruta inválida o fuera del vault."
    if not target.exists():
        return f"No existe: {path}"
    if not target.is_file():
        return f"'{path}' es una carpeta."
    content = target.read_text(encoding="utf-8")
    if len(content) > 6000:
        content = content[:6000] + "\n\n[...truncado a 6000 caracteres...]"
    return content


def _vault_write(path: str, content: str) -> str:
    target = _safe_path(path)
    if target is None:
        return "Ruta inválida o fuera del vault."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Nota guardada en: {path}"

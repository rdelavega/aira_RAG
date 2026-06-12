import asyncio
import os
import anthropic
from tools import execute_tool, TOOL_DEFINITIONS
from ctx import get_history, add_exchange

MODEL = os.getenv("AGENT_MODEL", "anthropic/claude-haiku-4-5").replace("anthropic/", "")

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """\
Eres Aira, asistente personal de investigación. Responde SIEMPRE en español, \
sin importar el idioma en que te escriban.

## Herramientas disponibles

- `query_rag` — para preguntas sobre libros, notas o investigaciones del vault de Obsidian. \
SIEMPRE úsalo antes de buscar en internet cuando la pregunta sea sobre contenido del usuario.
- `web_search` — para información actual, noticias o datos que no están en las notas.
- `vault_list` — para mostrar la estructura de carpetas del vault.
- `vault_read` — SOLO cuando el usuario pide ver literalmente el contenido de una nota concreta.
- `vault_write` — para crear o actualizar notas. Siempre confirma antes de sobreescribir.

## Prioridad de fuentes

1. Si la pregunta es sobre libros o notas del usuario → `query_rag` primero.
2. Si el RAG no tiene la información → `web_search`.
3. Nunca mezcles información del vault con información web sin aclararlo.

## Ingesta de documentos

- Si el usuario quiere añadir un libro o documento, dile que lo envíe como archivo PDF \
directamente en este chat. No necesita ningún comando especial.
- Puede añadir el nombre de una carpeta del vault como descripción del archivo para \
que las notas se guarden ahí. Sin descripción va a `00_INBOX`.

## Límites

- No borres ni sobreescribas archivos sin confirmación explícita del usuario.
- No accedas a rutas fuera del vault.
- Respuestas concisas. No des explicaciones innecesariamente largas.\
"""


async def run_agent(user_id: str, user_message: str) -> str:
    messages = get_history(user_id) + [{"role": "user", "content": user_message}]

    while True:
        response = await asyncio.to_thread(
            client.messages.create,
            model=MODEL,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            max_tokens=1024,
        )

        if response.stop_reason == "end_turn":
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            add_exchange(user_id, user_message, text)
            return text or "(sin respuesta)"

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })
            messages.append({"role": "user", "content": results})
            continue

        return "Error inesperado del agente."

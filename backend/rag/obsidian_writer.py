import anthropic
import asyncio
import os
import re
from datetime import datetime

ANALYSIS_PROVIDER = os.getenv("ANALYSIS_PROVIDER", "anthropic")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Haiku 4.5 pricing per million tokens
_PRICE_INPUT = 0.80
_PRICE_OUTPUT = 4.00

_token_stats: dict = {
    "input_tokens": 0,
    "output_tokens": 0,
    "api_calls": 0,
    "estimated_cost_usd": 0.0,
}


def get_token_stats() -> dict:
    return dict(_token_stats)


def _record_usage(input_tokens: int, output_tokens: int) -> None:
    _token_stats["input_tokens"] += input_tokens
    _token_stats["output_tokens"] += output_tokens
    _token_stats["api_calls"] += 1
    _token_stats["estimated_cost_usd"] = round(
        _token_stats["input_tokens"] / 1_000_000 * _PRICE_INPUT
        + _token_stats["output_tokens"] / 1_000_000 * _PRICE_OUTPUT,
        6,
    )


async def _generate(prompt: str, max_tokens: int) -> str:
    """Route to Claude or Ollama based on ANALYSIS_PROVIDER."""
    if ANALYSIS_PROVIDER == "ollama":
        from langchain_ollama import OllamaLLM
        model = OllamaLLM(
            model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
            base_url=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"),
            num_predict=max_tokens,
            temperature=0.3,
        )
        return await asyncio.to_thread(model.invoke, prompt)

    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    _record_usage(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text


async def write_book_to_vault(pdf_path: str, book_name: str, vault_path: str, target_folder: str = None) -> dict:

    from rag.populate_database import extract_text_from_pdf

    full_text = extract_text_from_pdf(pdf_path)

    chapters = split_into_chapters(full_text)

    clean_name = re.sub(r"[^\w\s-]", "", book_name.replace(".pdf", "")).strip()
    if target_folder:
        safe_folder = re.sub(r"[^\w\s\-/]", "", target_folder).strip().strip("/")
        book_folder = f"{vault_path}/{safe_folder}/Borradores_IA/{clean_name}"
    else:
        book_folder = f"{vault_path}/00_INBOX/Borradores_IA/{clean_name}"
    chapters_folder = f"{book_folder}/Capitulos"
    os.makedirs(chapters_folder, exist_ok=True)

    chapter_summaries = []

    for i, chapter_text in enumerate(chapters, 1):
        summary = await analyze_chapter(chapter_text, i, clean_name)
        chapter_summaries.append(summary)

        md_path = f"{chapters_folder}/Cap{i:02d}.md"
        with open(md_path, "w") as f:
            f.write(
                f"---\ntags: [\"#nota/capitulo\", \"#borrador\"]\nlibro: {clean_name}\ncapitulo: {i}\nfecha: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n"
            )
            f.write(summary)

    global_analysis = await analyze_global(chapter_summaries, clean_name)
    with open(f"{book_folder}/00_Global.md", "w") as f:
        f.write(
            f'---\ntags: ["#nota/resumen_global", "#borrador"]\nlibro: {clean_name}\n---\n\n'
        )
        f.write(global_analysis)

    exam = await generate_exam(global_analysis, clean_name)
    with open(f"{book_folder}/00_Examen.md", "w") as f:
        f.write(
            f'---\ntags: ["#nota/examen", "#borrador"]\nlibro: {clean_name}\n---\n\n'
        )
        f.write(exam)

    return {
        "chapters": len(chapters),
        "exam_questions": 30,
        "vault_path": f"00_INBOX/Borradores_IA/{clean_name}",
    }


async def analyze_chapter(text: str, num: int, book_name: str) -> str:
    prompt = f"""Analiza este capítulo del libro "{book_name}" y genera un resumen de 300-350 palabras en español.

Incluye:
- Idea central del capítulo
- 3-5 conceptos clave con definición breve
- Conexión con el resto del libro

Capítulo {num}:
{text[:4000]}"""
    result = await _generate(prompt, max_tokens=1000)
    return f"# Capítulo {num}\n\n{result}"


async def analyze_global(summaries: list, book_name: str) -> str:
    combined = "\n\n---\n\n".join(summaries[:10])
    prompt = f"""Con base en estos resúmenes del libro "{book_name}", genera:
1. Tesis central (1 párrafo)
2. Mapa de ideas principales
3. Aplicaciones prácticas (3-5 puntos)
4. Preguntas que deja abiertas

Resúmenes:
{combined}"""
    result = await _generate(prompt, max_tokens=2000)
    return f"# Análisis Global: {book_name}\n\n{result}"


async def generate_exam(global_analysis: str, book_name: str) -> str:
    prompt = f"""Genera un examen de 30 preguntas cerradas (opción múltiple, 4 opciones) sobre "{book_name}".

Reglas:
- Preguntas de comprensión, aplicación y análisis
- Respuesta correcta al final en sección separada
- Formato Markdown con numeración clara

Contexto:
{global_analysis[:3000]}"""
    result = await _generate(prompt, max_tokens=3000)
    return f"# Examen: {book_name}\n\n{result}"


def split_into_chapters(text: str) -> list:
    import re

    pattern = r"\n(?:CAPÍTULO|CAPITULO|Chapter|CHAPTER|Cap\.?)\s+\w+"
    parts = re.split(pattern, text, flags=re.IGNORECASE)

    if len(parts) > 2:
        return [p.strip() for p in parts if len(p.strip()) > 500]

    words = text.split()
    chunk_size = 3000
    return [
        " ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)
    ]

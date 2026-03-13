# import anthropic
import asyncio
import os
import re
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


async def write_book_to_vault(pdf_path: str, book_name: str, vault_path: str) -> dict:
    """Genera notas por capítulo + global + examen y las guarda en el vault"""

    # Leer texto del PDF (ya lo tienes en tu pipeline)
    from rag.populate_database import extract_text_from_pdf

    full_text = extract_text_from_pdf(pdf_path)

    # Detectar capítulos
    chapters = split_into_chapters(full_text)

    clean_name = re.sub(r"[^\w\s-]", "", book_name.replace(".pdf", ""))
    book_folder = f"{vault_path}/00_INBOX/Borradores_IA/{clean_name}"
    chapters_folder = f"{book_folder}/Capitulos"
    os.makedirs(chapters_folder, exist_ok=True)

    chapter_summaries = []

    # 1. Analizar cada capítulo
    for i, chapter_text in enumerate(chapters, 1):
        summary = await analyze_chapter(chapter_text, i, clean_name)
        chapter_summaries.append(summary)

        md_path = f"{chapters_folder}/Cap{i:02d}.md"
        with open(md_path, "w") as f:
            f.write(
                f"---\ntags: [\"#nota/capitulo\", \"#borrador\"]\nlibro: {clean_name}\ncapitulo: {i}\nfecha: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n"
            )
            f.write(summary)

    # 2. Análisis global
    global_analysis = await analyze_global(chapter_summaries, clean_name)
    with open(f"{book_folder}/00_Global.md", "w") as f:
        f.write(
            f'---\ntags: ["#nota/resumen_global", "#borrador"]\nlibro: {clean_name}\n---\n\n'
        )
        f.write(global_analysis)

    # 3. Examen
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
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-5",  # más rápido y barato
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"""Analiza este capítulo...{text[:4000]}"""}
        ],
    )
    return f"# Capítulo {num}\n\n{response.content[0].text}"


async def analyze_global(summaries: list, book_name: str) -> str:
    combined = "\n\n---\n\n".join(summaries[:10])
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""Análisis global...{combined}"""}],
    )
    return f"# Análisis Global: {book_name}\n\n{response.content[0].text}"


async def generate_exam(global_analysis: str, book_name: str) -> str:
    response = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-5",
        max_tokens=3000,
        messages=[
            {"role": "user", "content": f"""Genera examen...{global_analysis[:3000]}"""}
        ],
    )
    return f"# Examen: {book_name}\n\n{response.content[0].text}"


def split_into_chapters(text: str) -> list:
    """Divide el texto en capítulos por headings o tamaño"""
    import re

    # Intenta dividir por capítulos reales
    pattern = r"\n(?:CAPÍTULO|CAPITULO|Chapter|CHAPTER|Cap\.?)\s+\w+"
    parts = re.split(pattern, text, flags=re.IGNORECASE)

    if len(parts) > 2:
        return [p.strip() for p in parts if len(p.strip()) > 500]

    # Fallback: chunks de ~3000 palabras
    words = text.split()
    chunk_size = 3000
    return [
        " ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)
    ]

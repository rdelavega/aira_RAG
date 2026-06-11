import asyncio
import logging
import os
import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from agent import run_agent
from ctx import clear_history

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
RAG_URL = os.getenv("RAG_URL", "http://fastapi:8000")
MAX_MSG_LEN = 4000  # Telegram limit is 4096

_raw_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USERS: set[str] = set(filter(None, _raw_allowed.split(","))) if _raw_allowed else set()


def _is_allowed(user_id: str) -> bool:
    return not ALLOWED_USERS or user_id in ALLOWED_USERS


async def _safe_reply(message, text: str):
    text = text[:MAX_MSG_LEN]
    try:
        await message.reply_text(text, parse_mode="Markdown")
    except Exception:
        await message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not _is_allowed(user_id):
        return
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        response = await run_agent(user_id, update.message.text)
        await _safe_reply(update.message, response)
    except Exception as e:
        logger.error(f"Error en handle_message user={user_id}: {e}")
        await update.message.reply_text("Ocurrió un error. Por favor intenta de nuevo.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(str(update.effective_user.id)):
        return
    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Solo acepto archivos PDF por esta vía.")
        return

    await update.message.reply_text("📄 PDF recibido, iniciando procesamiento...")

    try:
        tg_file = await doc.get_file()
        tmp_path = f"/tmp/{doc.file_name}"
        await tg_file.download_to_drive(tmp_path)

        async with httpx.AsyncClient(timeout=15) as client:
            with open(tmp_path, "rb") as f:
                resp = await client.post(
                    f"{RAG_URL}/upload",
                    files={"files": (doc.file_name, f, "application/pdf")},
                )
            resp.raise_for_status()
            data = resp.json()

        jobs = data.get("jobs", [])
        if not jobs:
            await update.message.reply_text("❌ Error al iniciar el procesamiento.")
            return

        job_id = jobs[0]["job_id"]

        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(600):
                await asyncio.sleep(3)
                resp = await client.get(f"{RAG_URL}/jobs/{job_id}")
                job = resp.json()
                status = job.get("status")
                if status == "done":
                    vault_path = (job.get("result") or {}).get("vault_path", "")
                    msg = "✅ PDF indexado. Ya puedes preguntarme sobre su contenido."
                    if vault_path:
                        msg += f"\n📁 Notas en: `{vault_path}`"
                    await update.message.reply_text(msg, parse_mode="Markdown")
                    return
                if status == "error":
                    await update.message.reply_text("❌ Error al procesar el PDF. Intenta subirlo de nuevo.")
                    return

        await update.message.reply_text("⏱ El procesamiento está tardando. Intenta más tarde.")

    except Exception as e:
        logger.error(f"Error procesando PDF: {e}")
        await update.message.reply_text("❌ Error al procesar el archivo.")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy Aira, tu asistente de investigación personal.\n\n"
        "Puedo responder preguntas sobre tus notas y libros, buscar en internet "
        "y gestionar tu vault de Obsidian.\n\n"
        "Comandos:\n"
        "/reset — reiniciar el contexto de la conversación"
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_allowed(str(update.effective_user.id)):
        return
    clear_history(str(update.effective_user.id))
    await update.message.reply_text("🔄 Contexto reiniciado. ¿En qué te ayudo?")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    model = os.getenv("AGENT_MODEL", "claude-haiku-4-5")
    if ALLOWED_USERS:
        logger.info(f"Aira bot iniciado (model: {model}, usuarios permitidos: {ALLOWED_USERS})")
    else:
        logger.warning(f"Aira bot iniciado (model: {model}, SIN RESTRICCION DE USUARIOS)")
    app.run_polling()


if __name__ == "__main__":
    main()

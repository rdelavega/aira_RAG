FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir anthropic "python-telegram-bot[all]" httpx
COPY . .
CMD ["python", "bot.py"]

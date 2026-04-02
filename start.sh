#!/bin/bash
# start.sh — Initates AIRA

set -e

echo "Inicializing AIRA..."

# Verificar .env
if [ ! -f .env ]; then
    echo "Error, there's no .env file — copy .env.example and fill with your config"
    exit 1
fi

# Verificar vault path
source .env
if [ ! -d "$VAULT_PATH" ]; then
    echo "Vault not found on: $VAULT_PATH"
    echo "Check VAULT_PATH on your .env"
    exit 1
fi

mkdir -p "$VAULT_PATH/10_Books"
mkdir -p "$VAULT_PATH/20_Design"
mkdir -p "$VAULT_PATH/30_Business"
mkdir -p "$VAULT_PATH/40_Personal"
mkdir -p "$VAULT_PATH/90_Archive"

echo "Vault verified: $VAULT_PATH"

docker compose up -d

echo ""
echo "AIRA iniciated.."
echo "   API RAG:   http://localhost:8000"
echo "   OpenClaw:  http://localhost:18789"
echo "   Ollama:    http://localhost:11434"
echo ""
echo "Logs: docker compose logs -f"
echo "Stop: docker compose down"
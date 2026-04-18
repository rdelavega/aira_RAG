#!/bin/bash
# start.sh — Initates AIRA

set -e

# #region agent log
_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_agent_log="$_script_dir/debug-11adcd.log"
_plen=$(pwd | wc -c | tr -d ' ')
_he=0; [ -f .env ] && _he=1
_esd=0; [ -f "$_script_dir/.env" ] && _esd=1
printf '%s\n' "{\"sessionId\":\"11adcd\",\"hypothesisId\":\"H1\",\"location\":\"start.sh:entry\",\"message\":\"cwd and env file\",\"data\":{\"pwd_len\":${_plen},\"env_in_cwd\":${_he},\"env_in_script_dir\":${_esd}},\"timestamp\":$(($(date +%s)*1000))}" >> "$_agent_log" 2>/dev/null || true
# #endregion

echo "Inicializing AIRA..."

# Verificar .env
if [ ! -f .env ]; then
    echo "Error, there's no .env file — copy .env.example and fill with your config"
    exit 1
fi

# Verificar vault path
source .env
# #region agent log
_vnz=0; [ -n "${VAULT_PATH:-}" ] && _vnz=1
_vid=0; [ -n "${VAULT_PATH:-}" ] && [ -d "$VAULT_PATH" ] && _vid=1
printf '%s\n' "{\"sessionId\":\"11adcd\",\"hypothesisId\":\"H3\",\"location\":\"start.sh:after-source\",\"message\":\"vault env\",\"data\":{\"vault_nonempty\":${_vnz},\"vault_isdir\":${_vid}},\"timestamp\":$(($(date +%s)*1000))}" >> "$_agent_log" 2>/dev/null || true
# #endregion
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

# #region agent log
_dc=0; command -v docker >/dev/null 2>&1 && _dc=1
_dcv=0; docker compose version >/dev/null 2>&1 && _dcv=1
printf '%s\n' "{\"sessionId\":\"11adcd\",\"hypothesisId\":\"H4\",\"location\":\"start.sh:pre-compose\",\"message\":\"docker cli\",\"data\":{\"docker_bin\":${_dc},\"compose_subcmd_ok\":${_dcv}},\"timestamp\":$(($(date +%s)*1000))}" >> "$_agent_log" 2>/dev/null || true
# #endregion
docker compose up -d

echo ""
echo "AIRA iniciated.."
echo "   API RAG:   http://localhost:8000"
echo "   OpenClaw:  http://localhost:18789"
echo "   Ollama:    http://localhost:11434"
echo ""
echo "Logs: docker compose logs -f"
echo "Stop: docker compose down"
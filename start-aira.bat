@echo off
title AIRA - Iniciando...
echo.
echo  ╔═══════════════════════════════════╗
echo  ║       AIRA - Asistente IA         ║
echo  ║       Iniciando sistema...        ║
echo  ╚═══════════════════════════════════╝
echo.
cd /d "%~dp0"

echo [1/2] Verificando Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker no esta corriendo. Por favor abre Docker Desktop primero.
    pause
    exit /b 1
)

echo [2/2] Iniciando AIRA...
docker compose up -d

echo.
echo  ╔═══════════════════════════════════╗
echo  ║   AIRA iniciado correctamente!    ║
echo  ║   Ya puedes usar el bot en        ║
echo  ║   Telegram.                       ║
echo  ╚═══════════════════════════════════╝
echo.
timeout /t 3 >nul
@echo off
title AIRA - Iniciando...
cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║        AIRA - Asistente IA            ║
echo  ╚═══════════════════════════════════════╝
echo.

REM ── 1. Verificar .env ────────────────────────────────────────
if not exist ".env" (
    echo  [!] No se encontro el archivo .env
    echo.
    echo  Copiando .env.example a .env...
    copy ".env.example" ".env" >nul
    echo  Abriendo .env en el Bloc de notas...
    echo  Completa los valores y guarda el archivo.
    echo.
    notepad ".env"
    echo.
    echo  Cuando hayas guardado .env, vuelve a ejecutar start-aira.bat
    pause
    exit /b 0
)

REM ── Verificar que .env no tenga valores de ejemplo sin reemplazar ──
findstr /C:"sk-ant-..." ".env" >nul 2>&1
if not errorlevel 1 (
    echo  [!] El archivo .env todavia tiene valores de ejemplo.
    echo  Abriendo .env para que lo completes...
    notepad ".env"
    echo.
    echo  Cuando hayas guardado .env con tus datos reales, vuelve a ejecutar start-aira.bat
    pause
    exit /b 0
)

REM ── 2. Verificar Docker ───────────────────────────────────────
echo  [1/3] Verificando Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Docker Desktop no esta corriendo.
    echo.
    echo  Solucion:
    echo    1. Abre Docker Desktop desde el menu de inicio
    echo    2. Espera a que el icono de la ballena este verde
    echo    3. Vuelve a ejecutar start-aira.bat
    echo.
    pause
    exit /b 1
)
echo         OK

REM ── 3. Verificar Ollama ───────────────────────────────────────
echo  [2/3] Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERROR] Ollama no esta corriendo.
    echo.
    echo  Solucion:
    echo    1. Abre Ollama desde el menu de inicio
    echo    2. Espera a que el icono de la llama aparezca en la barra de tareas
    echo    3. Vuelve a ejecutar start-aira.bat
    echo.
    pause
    exit /b 1
)
echo         OK

REM ── 4. Iniciar servicios ──────────────────────────────────────
echo  [3/3] Iniciando AIRA...
docker compose up -d
if errorlevel 1 (
    echo.
    echo  [ERROR] No se pudo iniciar AIRA.
    echo  Revisa los logs: docker compose logs
    pause
    exit /b 1
)

echo.
echo  ╔═══════════════════════════════════════╗
echo  ║   AIRA iniciado correctamente.        ║
echo  ║   Ya puedes usar el bot en Telegram.  ║
echo  ╚═══════════════════════════════════════╝
echo.
timeout /t 4 >nul

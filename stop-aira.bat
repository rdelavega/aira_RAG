@echo off
title AIRA - Deteniendo...
echo.
echo  ╔═══════════════════════════════════╗
echo  ║       AIRA - Deteniendo...        ║
echo  ╚═══════════════════════════════════╝
echo.
cd /d "%~dp0"
docker compose down
echo.
echo  AIRA detenido correctamente.
echo.
timeout /t 3 >nul
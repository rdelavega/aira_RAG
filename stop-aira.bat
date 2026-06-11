@echo off
title AIRA - Deteniendo...
cd /d "%~dp0"

echo.
echo  Deteniendo AIRA...
docker compose down
echo.
echo  AIRA detenido correctamente.
echo.
timeout /t 3 >nul

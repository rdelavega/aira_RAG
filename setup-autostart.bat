@echo off
title AIRA - Configurando autoarranque...
echo.
echo  ╔═══════════════════════════════════╗
echo  ║   Configurando AIRA autostart     ║
echo  ╚═══════════════════════════════════╝
echo.

REM Crear tarea en el Programador de tareas
schtasks /create /tn "AIRA Autostart" /tr "%~dp0start-aira.bat" /sc onlogon /rl highest /f

if errorlevel 1 (
    echo ERROR: No se pudo configurar el autoarranque.
    echo Intenta ejecutar este archivo como Administrador.
    pause
    exit /b 1
)

echo.
echo  ✓ AIRA configurado para arrancar automaticamente
echo    al iniciar Windows.
echo.
echo  Para desactivar el autoarranque, ejecuta:
echo  schtasks /delete /tn "AIRA Autostart" /f
echo.
pause
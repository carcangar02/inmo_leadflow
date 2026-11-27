@echo off
title InmoLeadFlow - Servidor Demo Villaviciosa
cd /d "%~dp0"
echo ===================================================
echo   InmoLeadFlow - Demo Consulting Inmobiliario Odon
echo ===================================================
echo Activando entorno virtual...
call .\venv\Scripts\activate.bat
echo Iniciando servidor en http://localhost:8120
echo Dashboard CRM: http://localhost:8120/dashboard
echo Para abrir desde tu movil en la misma WiFi: http://[TU_IP_LOCAL]:8120
echo.
.\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8120 --reload
pause

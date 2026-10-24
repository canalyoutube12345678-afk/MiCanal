@echo off
REM Uso: producir_windows.bat 0001_zara   (nombre de la carpeta dentro de videos\)
cd /d "%~dp0"
.venv\Scripts\python scripts\producir.py videos\%1
pause

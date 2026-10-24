@echo off
REM Instala todo lo necesario en Windows 10/11 (ejecutar una sola vez, doble clic).
cd /d "%~dp0"
where python >nul 2>nul || winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
where ffmpeg >nul 2>nul || winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
echo.
echo Si acaba de instalarse Python o FFmpeg, CIERRA esta ventana y vuelve a ejecutar este archivo.
echo.
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
echo.
echo Listo. Prueba con:  .venv\Scripts\python scripts\producir.py videos\0000_prueba_chupa_chups
pause

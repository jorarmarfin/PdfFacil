@echo off
REM Ejecuta PDF Facil en Windows (crea .venv e instala dependencias la primera vez).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)
.venv\Scripts\python.exe pdf_facil.py %*

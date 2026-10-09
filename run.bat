@echo off
REM Ejecuta PDF Facil en Windows. Requiere Python 3.12+ (python.org, con "Add to PATH" o launcher py).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if not exist ".venv\Scripts\python.exe" (
    echo No se encontro Python 3.12+. Instalalo desde https://www.python.org/downloads/
    pause
    exit /b 1
  )
)
if not exist ".venv\.deps_ok" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || (
    echo Error instalando dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
  )
  echo ok> ".venv\.deps_ok"
)
".venv\Scripts\python.exe" pdf_facil.py %*
if errorlevel 1 pause

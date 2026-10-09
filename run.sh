#!/usr/bin/env bash
# Ejecuta PDF Fácil en Linux/macOS (crea .venv e instala dependencias la primera vez).
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
exec .venv/bin/python pdf_facil.py "$@"

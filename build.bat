@echo off
REM Compila ZIP + instalador en Windows. Argumentos: los mismos de build.ps1 (ej. -Version 1.0.1 -SkipTests)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
if errorlevel 1 pause

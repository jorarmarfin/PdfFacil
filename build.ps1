<#
Compila PDFacil en Windows: onedir (PyInstaller) + ZIP portable + instalador (Inno Setup).
Uso:  .\build.ps1 [-Version 1.0.0] [-SkipTests] [-SkipInstaller]
Salida: PDF_Facil-Windows-x64.zip e installer_output\PDFacil-Setup-<version>.exe (+ .sha256)
#>
param(
    [string]$Version,
    [switch]$SkipTests,
    [switch]$SkipInstaller
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Run($exe, $argList) {
    & $exe @argList
    if ($LASTEXITCODE -ne 0) { throw "Falló: $exe $($argList -join ' ')" }
}

if (-not $Version) {
    $Version = (Select-String -Path app\version.py -Pattern '^__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
}
Write-Host "== PDFacil $Version ==" -ForegroundColor Cyan

# 1. Entorno
if (-not (Test-Path .venv\Scripts\python.exe)) {
    Write-Host "Creando .venv..."
    & py -3.12 -m venv .venv
    if (-not (Test-Path .venv\Scripts\python.exe)) { & python -m venv .venv }
}
$py = (Resolve-Path .venv\Scripts\python.exe).Path
Run $py @("-m","pip","install","-q","-r","requirements.lock","pyinstaller")

# 2. Pruebas
if (-not $SkipTests) {
    $env:QT_QPA_PLATFORM = "offscreen"
    Run $py @("-m","pytest","-q")
    Remove-Item Env:QT_QPA_PLATFORM
}

# 3. PyInstaller onedir
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Run $py @("-m","PyInstaller","--noconfirm","--clean","--windowed","--onedir","--name","PDF_Facil",
          "--icon","assets/icon.ico","--add-data","assets;assets","pdf_facil.py")
if (-not (Test-Path dist\PDF_Facil\PDF_Facil.exe)) { throw "Falta PDF_Facil.exe" }
if (-not (Test-Path dist\PDF_Facil\_internal))     { throw "Falta _internal" }

# 4. ZIP portable + SHA-256
$zip = "PDF_Facil-Windows-x64.zip"
Remove-Item $zip -ErrorAction SilentlyContinue
Copy-Item README.md dist\PDF_Facil\LEEME.md -Force
Compress-Archive -Path dist\PDF_Facil -DestinationPath $zip
$h = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
"$h  $zip" | Out-File -Encoding ascii "$zip.sha256"
Write-Host "ZIP: $zip  SHA-256 $h"

# 5. Instalador
if (-not $SkipInstaller) {
    $iscc = @(
        (Get-Command iscc -ErrorAction SilentlyContinue).Source,
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $iscc) { throw "No se encontró Inno Setup 6. Instala: winget install JRSoftware.InnoSetup" }
    Run $iscc @("/DAppVersion=$Version", "installer\PDFacil.iss")
    $setup = "installer_output\PDFacil-Setup-$Version.exe"
    if (-not (Test-Path $setup)) { throw "Falta $setup" }
    $h = (Get-FileHash $setup -Algorithm SHA256).Hash.ToLower()
    "$h  PDFacil-Setup-$Version.exe" | Out-File -Encoding ascii "$setup.sha256"
    Write-Host "Instalador: $setup  SHA-256 $h"
}
Write-Host "Listo." -ForegroundColor Green

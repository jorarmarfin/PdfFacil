<#
Construye el paquete MSIX x64 de PDFácil a partir de dist\PDF_Facil (PyInstaller --onedir).
Herramientas oficiales: makeappx.exe (Windows SDK) y, si existe, Windows App Certification Kit.
El .msix resultante NO se firma: Microsoft Store lo firma al publicar.

Uso:
  .\tools\build_msix.ps1 -IdentityName <Partner Center> -Publisher "CN=..." -PublisherDisplayName <Partner Center>
Sin los tres parámetros se genera un paquete de PRUEBA (identidad local) que no sirve para la Store.
#>
param(
    [string]$IdentityName,
    [string]$Publisher,
    [string]$PublisherDisplayName,
    [string]$DisplayName = "PDFácil",
    [string]$Version,
    [string]$Source = "dist\PDF_Facil",
    [string]$Output = "msix_output"
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $Version) {
    $Version = (Select-String -Path app\version.py -Pattern '^__version__\s*=\s*"([^"]+)"').Matches[0].Groups[1].Value
}
# MSIX exige 4 partes; la Store reserva la cuarta (revisión) = 0.
$parts = $Version.Split('.')
if ($parts.Count -ne 3) { throw "Versión '$Version' debe ser X.Y.Z" }
$msixVersion = "$Version.0"

$storeReady = [bool]($IdentityName -and $Publisher -and $PublisherDisplayName)
if (-not $storeReady) {
    Write-Warning "Faltan datos de Partner Center: se genera un paquete de PRUEBA, no subir a la Store."
    $IdentityName = "Hefesto2JS.PDFacilTest"
    $Publisher = "CN=PDFacilLocalTest"
    $PublisherDisplayName = "Hefesto2JS"
}
if ($Publisher -notmatch '^CN=') { throw "Publisher debe ser el valor de Partner Center, tipo 'CN=...'" }

if (-not (Test-Path "$Source\PDF_Facil.exe")) { throw "Falta $Source\PDF_Facil.exe (ejecuta PyInstaller antes)" }

# Localiza makeappx.exe del Windows SDK (la versión más reciente x64).
$makeappx = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\makeappx.exe" -ErrorAction SilentlyContinue |
    Sort-Object { [version]($_.Directory.Parent.Name) } -Descending | Select-Object -First 1
if (-not $makeappx) { throw "makeappx.exe no encontrado: instala el Windows 10/11 SDK" }
Write-Host "makeappx: $($makeappx.FullName)"

$layout = Join-Path $Output "layout"
Remove-Item -Recurse -Force $Output -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $layout | Out-Null
Copy-Item "$Source\*" $layout -Recurse -Force

python tools\make_msix_assets.py (Join-Path $layout "Images")
if ($LASTEXITCODE -ne 0) { throw "No se pudieron generar los logos" }

$esc = { param($s) [System.Security.SecurityElement]::Escape($s) }
$xml = Get-Content msix\AppxManifest.xml.template -Raw -Encoding UTF8
$xml = $xml.Replace("{{IDENTITY_NAME}}", (& $esc $IdentityName)).Replace("{{PUBLISHER}}", (& $esc $Publisher)).
    Replace("{{PUBLISHER_DISPLAY_NAME}}", (& $esc $PublisherDisplayName)).Replace("{{DISPLAY_NAME}}", (& $esc $DisplayName)).
    Replace("{{VERSION}}", $msixVersion)
[IO.File]::WriteAllText((Join-Path $layout "AppxManifest.xml"), $xml, (New-Object Text.UTF8Encoding($false)))

$name = if ($storeReady) { "PDFacil_${msixVersion}_x64.msix" } else { "PDFacil_${msixVersion}_x64_TEST.msix" }
$msix = Join-Path $Output $name
& $makeappx.FullName pack /d $layout /p $msix /o
if ($LASTEXITCODE -ne 0) { throw "makeappx pack falló" }

# Validación estructural con la herramienta oficial (esquema del manifiesto y archivos referenciados).
& $makeappx.FullName unpack /p $msix /d (Join-Path $Output "verify") /o | Out-Null
if ($LASTEXITCODE -ne 0) { throw "makeappx unpack (verificación) falló" }
Remove-Item -Recurse -Force (Join-Path $Output "verify")

$h = (Get-FileHash $msix -Algorithm SHA256).Hash.ToLower()
"$h  $name" | Out-File -Encoding ascii "$msix.sha256"
Write-Host "OK: $msix ($([math]::Round((Get-Item $msix).Length/1MB,1)) MB) SHA-256 $h"
if ($env:GITHUB_OUTPUT) {
    "msix=$msix" >> $env:GITHUB_OUTPUT
    "store_ready=$($storeReady.ToString().ToLower())" >> $env:GITHUB_OUTPUT
    "publisher=$Publisher" >> $env:GITHUB_OUTPUT
}

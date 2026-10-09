<#
Prueba funcional del MSIX dentro del contenedor (solo CI / máquina de pruebas).
Firma una COPIA con un certificado temporal (nunca el paquete de la Store), la instala,
ejecuta `PDFFacil.exe --selftest` (selección, lectura, unión, compresión, guardado) y lo desinstala.
El certificado temporal se elimina al terminar; no es una solución de producción.
Uso: .\tools\test_msix.ps1 -Msix msix_output\PDFacil_1.1.0.0_x64.msix
#>
param([Parameter(Mandatory)][string]$Msix)
$ErrorActionPreference = "Stop"
$Msix = (Resolve-Path $Msix).Path
$work = Join-Path $env:RUNNER_TEMP "msixtest"; if (-not $env:RUNNER_TEMP) { $work = Join-Path $env:TEMP "msixtest" }
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
New-Item -ItemType Directory $work | Out-Null

# Publisher exacto del manifiesto, para que la firma de prueba coincida.
$mk = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\makeappx.exe" | Sort-Object FullName -Descending | Select-Object -First 1
$signtool = Join-Path $mk.Directory.FullName "signtool.exe"
& $mk.FullName unpack /p $Msix /d (Join-Path $work "m") /o | Out-Null
[xml]$man = Get-Content (Join-Path $work "m\AppxManifest.xml")
$subject = $man.Package.Identity.Publisher
$pfn = $man.Package.Identity.Name

$cert = New-SelfSignedCertificate -Type Custom -Subject $subject -KeyUsage DigitalSignature -FriendlyName "PDFacil CI test" `
    -CertStoreLocation "Cert:\CurrentUser\My" -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$signed = Join-Path $work "test-signed.msix"
Copy-Item $Msix $signed
try {
    $pwd = ConvertTo-SecureString "ci-temp" -AsPlainText -Force
    $pfx = Join-Path $work "t.pfx"
    Export-PfxCertificate -Cert $cert -FilePath $pfx -Password $pwd | Out-Null
    & $signtool sign /fd SHA256 /f $pfx /p "ci-temp" $signed
    if ($LASTEXITCODE -ne 0) { throw "signtool falló" }
    Import-Certificate -FilePath (Export-Certificate -Cert $cert -FilePath (Join-Path $work "t.cer")).FullName `
        -CertStoreLocation Cert:\LocalMachine\TrustedPeople | Out-Null

    Add-AppxPackage -Path $signed
    $pkg = Get-AppxPackage -Name $pfn
    if (-not $pkg) { throw "El paquete no se instaló" }
    Write-Host "Instalado: $($pkg.PackageFullName)"

    $out = Join-Path $work "out"
    $alias = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\PDFFacil.exe"
    $p = Start-Process $alias -ArgumentList @("--selftest", "`"$out`"") -PassThru -Wait
    $json = Join-Path $out "selftest.json"
    if (-not (Test-Path $json)) { throw "No se generó selftest.json (exit $($p.ExitCode))" }
    Get-Content $json -Raw | Write-Host
    if (-not ((Get-Content $json -Raw | ConvertFrom-Json).ok)) { throw "La autoprueba dentro del MSIX falló" }
    if (-not (Test-Path (Join-Path $out "work\unido.pdf"))) { throw "No se guardó el PDF unido" }
    Write-Host "OK: PDFácil funciona dentro del contenedor MSIX"
}
finally {
    Get-AppxPackage -Name $pfn | Remove-AppxPackage -ErrorAction SilentlyContinue
    Get-ChildItem Cert:\LocalMachine\TrustedPeople | Where-Object Thumbprint -eq $cert.Thumbprint | Remove-Item -ErrorAction SilentlyContinue
    Remove-Item $cert.PSPath -ErrorAction SilentlyContinue
}

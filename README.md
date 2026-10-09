<p align="center"><img src="logo.png" alt="PDFácil" height="90"></p>

# PDF Fácil

Une varios PDF en el orden que tú elijas, sin renombrar archivos. Funciona sin internet y **nunca modifica tus originales**.

## Información del sistema

| | |
|---|---|
| Aplicación | PDFácil (`PDF_Facil.exe`), versión en `app/version.py` |
| Tipo | Aplicación de escritorio, 100 % offline, sin telemetría |
| Funciones | Unir PDF en el orden elegido · Comprimir PDF (3 niveles) |
| Plataforma de uso | Windows 10/11 64 bits |
| Desarrollo | Linux / Windows, Python ≥ 3.12 |
| Lenguaje y UI | Python + PySide6 6.12.0 (Qt 6) |
| Dependencias | pypdf 6.19.0 (leer/unir/comprimir), Pillow 12.3.0 (recomprimir imágenes) |
| Empaquetado | PyInstaller `--onedir` → carpeta `PDF_Facil.exe` + `_internal` |
| Instalador | Inno Setup 6 (`installer/PDFacil.iss`), por usuario, sin admin |
| CI/CD | GitHub Actions (`build-windows.yml`, runner `windows-latest`) |
| Licencia | MIT |

**Requisitos para el usuario:** Windows 10/11 x64, ~250 MB libres. No necesita Python ni internet.

**Datos del usuario:** solo se guardan la última carpeta usada y la geometría de la ventana (`QSettings`, registro de Windows `HKCU\Software\PDFFacil`). Las contraseñas de PDF no se guardan. Los PDF originales nunca se modifican: unir y comprimir generan archivos nuevos.

### Estructura del proyecto
```
pdf_facil.py            punto de entrada
app/
  main.py               arranque, tema, ícono
  version.py            versión y datos del autor (cambiar aquí al publicar)
  resources.py          ruta de recursos (dev y PyInstaller)
  core/                 lógica PDF sin UI: inspector, validador, unión, compresión
  models/               PdfItem (archivo en la lista)
  services/             workers en hilo (unir/comprimir), archivos, ajustes
  ui/                   ventana principal, diálogo de compresión, tema, tabla
assets/                 icon.ico/png, logo.png (generados con tools/make_icon.py)
installer/PDFacil.iss   script de Inno Setup
build.ps1 / build.bat   compilación local en Windows (ZIP + instalador)
tests/                  pytest (unión, orden, validación, compresión, UI)
logo.png, logo-corto.png  logos originales
```
La lógica de `core/` no depende de Qt; los workers la ejecutan en segundo plano para no congelar la ventana y permiten cancelar.

## Uso (usuaria final, Windows 10/11)

1. Descomprime `PDF_Facil-Windows-x64.zip` (clic derecho → *Extraer todo*) en una carpeta, por ejemplo `Documentos\PDF_Facil`.
2. Abre `PDF_Facil.exe`. Puedes crear un acceso directo en el escritorio.
3. Arrastra tus PDF a la ventana (o usa **Agregar PDF** / **Agregar carpeta**).
4. Cambia el orden arrastrando filas o con **Subir** / **Bajar**.
5. Pulsa **UNIR PDF**, elige dónde guardar y listo. Al final puedes abrir el archivo o su carpeta.
6. Opcional: **Comprimir PDF…** reduce el tamaño de un PDF (nivel equilibrado recomendado). Crea un archivo nuevo `_comprimido.pdf`; el original no se toca.

Atajos: `Ctrl+O` agregar, `Ctrl+Shift+O` carpeta, `Supr` quitar, `Ctrl+↑/↓` mover, `Ctrl+Enter` unir.

### Aviso de Windows (SmartScreen)
El programa no está firmado digitalmente, por lo que Windows puede mostrar «Windows protegió su PC / editor desconocido». Es esperable en programas nuevos. Verifica que el ZIP viene de quien te lo entregó y compara su huella SHA-256 (`PDF_Facil-Windows-x64.zip.sha256`):

```powershell
Get-FileHash .\PDF_Facil-Windows-x64.zip -Algorithm SHA256
```
Si coincide: *Más información → Ejecutar de todas formas*. No desactives Defender ni SmartScreen.

### Notas
- Si un PDF tiene contraseña, se pide al agregarlo y no se guarda.
- Si un PDF tiene firma digital, se avisa: al unir, la firma se pierde o queda inválida.
- Formularios, enlaces y anotaciones pueden no conservarse en algunos PDF.

## Desarrollo (Ubuntu / Linux)

```bash
./run.sh                       # crea .venv, instala dependencias y abre la app
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q  # pruebas (usa Qt offscreen)
```
En Windows para desarrollo: `run.bat`.

## Compilar y publicar (GitHub Actions)
PyInstaller no compila de Linux a Windows; lo hace el workflow `build-windows` en un runner Windows.

- **Prueba sin publicar:** *Actions → build-windows → Run workflow*. Deja los artefactos descargables, no crea Release.
- **Release oficial:** al subir un tag `vX.Y.Z` el workflow ejecuta pruebas, PyInstaller `--onedir`, Inno Setup y verifica el instalador. Solo si todo pasa, publica la Release del tag con `PDFacil-Setup.exe`, `PDF_Facil-Windows-x64.zip` y sus `.sha256`. Si algo falla no se publica nada. El tag debe coincidir con `app/version.py`.
- **Permisos:** el build corre con `contents: read`; solo el job de publicación tiene `contents: write`.

### Publicar una versión nueva desde Ubuntu
```bash
# 1. Edita la versión en app/version.py (ej. "1.2.0"), commit y push
git add app/version.py && git commit -m "Versión 1.2.0" && git push
# 2. Crea y sube el tag (debe ser v + la misma versión)
git tag v1.2.0
git push origin v1.2.0
# 3. Sigue el avance en la pestaña Actions; al terminar aparece en Releases
```
Si el workflow falla: corrige, y para reutilizar el tag bórralo (`git tag -d v1.2.0 && git push origin :refs/tags/v1.2.0`) y créalo de nuevo.

### Enlace permanente de descarga
Siempre apunta a la última Release, porque el instalador mantiene el nombre fijo:
```
https://github.com/jorarmarfin/PdfFacil/releases/latest/download/PDFacil-Setup.exe
```
El ícono se regenera con `python tools/make_icon.py`.

### Instalador
El workflow también genera `PDFacil-Setup.exe` (Inno Setup, `installer/PDFacil.iss`): instala por usuario sin admin en `%LOCALAPPDATA%\Programs\PDFacil`, crea acceso en Inicio (y escritorio opcional), se registra en *Aplicaciones instaladas* y actualiza sobre versiones previas conservando la configuración (vive en el registro de usuario, no se borra). Versión = tag `vX.Y.Z` o `app/version.py`. El instalador no está firmado: SmartScreen puede avisar (*Más información → Ejecutar de todas formas*).

Compilación local en Windows (ZIP + instalador; requiere Inno Setup 6, `winget install JRSoftware.InnoSetup`):
```powershell
.\build.ps1                    # o build.bat; opciones: -Version 1.0.1 -SkipTests -SkipInstaller
```
Salida: `PDF_Facil-Windows-x64.zip` e `installer_output\PDFacil-Setup.exe`.

## Licencia
MIT. Dependencias: PySide6 (LGPL), pypdf (BSD).

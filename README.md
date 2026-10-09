# PDF Fácil

Une varios PDF en el orden que tú elijas, sin renombrar archivos. Funciona sin internet y **nunca modifica tus originales**.

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

## Compilar el .exe de Windows
PyInstaller no compila de Linux a Windows. Usa GitHub Actions: pestaña *Actions → build-windows → Run workflow* (o sube un tag `v1.0.0`). Descarga el artifact `PDF_Facil-Windows-x64` (ZIP + SHA-256). El ícono se regenera con `python tools/make_icon.py`.

### Instalador
El workflow también genera `PDFacil-Setup-<versión>.exe` (Inno Setup, `installer/PDFacil.iss`): instala por usuario sin admin en `%LOCALAPPDATA%\Programs\PDFacil`, crea acceso en Inicio (y escritorio opcional), se registra en *Aplicaciones instaladas* y actualiza sobre versiones previas conservando la configuración (vive en el registro de usuario, no se borra). Versión = tag `vX.Y.Z` o `pyproject.toml`. Con tag `v*` se publica en Releases junto al ZIP. El instalador no está firmado: SmartScreen puede avisar (*Más información → Ejecutar de todas formas*).

Compilación local en Windows:
```powershell
pip install -r requirements.lock
pyinstaller --noconfirm --clean --windowed --onedir --name PDF_Facil pdf_facil.py
```

## Licencia
MIT. Dependencias: PySide6 (LGPL), pypdf (BSD).

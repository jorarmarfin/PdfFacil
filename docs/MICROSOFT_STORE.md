# Publicar PDFácil en Microsoft Store (MSIX)

Motivo: la Store rechazó el EXE por la política **10.2.9** (sin firma digital aceptada). Un paquete **MSIX enviado a la Store lo firma Microsoft** con su certificado al publicarlo: no hace falta comprar certificado. El instalador Inno Setup y el ZIP portable de GitHub Releases no cambian (workflow `build-windows`).

> No uses certificados autofirmados para distribuir. El único certificado temporal del repo (`tools/test_msix.ps1`) firma una copia en el runner de CI solo para probar la instalación y se borra al terminar.

## 1. Registrar la app en Partner Center
1. Cuenta de desarrollador en <https://partner.microsoft.com/dashboard> (individual, pago único; la empresa/individuo verificado).
2. **Apps y juegos → Nuevo producto → Aplicación MSIX o PWA**.
3. **Reservar el nombre**: `PDFácil`. Debe coincidir con `DisplayName` del manifiesto.
4. Categoría: *Productividad* (o *Utilidades y herramientas*). Edad: cuestionario de clasificación (sin contenido sensible).
5. **Gestión del producto → Identidad del producto**: copia estos tres valores (no los inventes):

   | Partner Center | Variable de GitHub |
   |---|---|
   | Package/Identity/Name (p. ej. `12345Hefesto2JS.PDFcil`) | `MSIX_IDENTITY_NAME` |
   | Package/Identity/Publisher (`CN=XXXXXXXX-...`) | `MSIX_PUBLISHER` |
   | Package/Properties/PublisherDisplayName | `MSIX_PUBLISHER_DISPLAY_NAME` |

6. En GitHub: *Settings → Secrets and variables → Actions → Variables → New repository variable* (tres variables; no son secretos).

## 2. Ficha de Store (pestaña Store listings, español)
- Descripción: *Une y comprime archivos PDF sin internet, en el orden que elijas. Nunca modifica tus originales. Sin telemetría.*
- Capturas: mínimo 1 de 1366×768 o mayor (ventana principal con varios PDF).
- Logo de la Store 300×300 (`assets/icon.png` reescalado).
- Política de privacidad: URL pública (puedes decir "no recopila ni envía datos"; la app es offline).
- Notas para certificación: *Aplicación de escritorio empaquetada (runFullTrust) porque lee y escribe PDF en carpetas elegidas por el usuario mediante diálogos de archivo. No usa red.*
- Explica la capacidad restringida `runFullTrust` en el campo correspondiente de *Properties*/notas: es obligatoria para toda app Win32 empaquetada.

## 3. Construir el MSIX
- **CI (recomendado):** *Actions → build-msix → Run workflow*, o subir un tag `vX.Y.Z` (igual a `app/version.py`). El job: pruebas → PyInstaller onedir → `makeappx pack` + verificación `makeappx unpack` → prueba funcional dentro del contenedor → artefacto `PDFacil-MSIX` (`PDFacil_X.Y.Z.0_x64.msix` + `.sha256`).
- Si faltan las variables `MSIX_*`, el artefacto se llama `PDFacil-MSIX-TEST-no-subir`: no sirve para la Store.
- **Local (Windows con Windows SDK):** `.\tools\build_msix.ps1 -IdentityName ... -Publisher "CN=..." -PublisherDisplayName ...` tras `build.ps1`/PyInstaller.

### Qué comprueba la prueba en contenedor
`PDF_Facil.exe --selftest` (instalado como MSIX, ejecutado vía alias `PDFFacil.exe`) crea PDF, **selecciona** (carpeta → lista), **lee** (inspección), **une**, **comprime**, **guarda** y relee, usa QSettings y construye la ventana principal. Genera `selftest.json`; si algún paso falla, el job falla.

## 4. Subir y publicar
1. Descarga el artefacto `.msix` del run.
2. Partner Center → tu app → **Nuevo envío → Paquetes** → arrastra el `.msix`. Debe aceptarlo sin pedir firma (la Store firma).
3. Completa precios (gratis), disponibilidad, clasificación y ficha → **Enviar a certificación** (suele tardar 1–3 días).
4. Opcional antes: **Windows App Certification Kit** (`appcert.exe`) en tu PC con el paquete instalado para adelantar fallos de certificación.

## 5. Actualizar
1. Sube `app/version.py` (p. ej. `1.2.0`), commit, tag `v1.2.0`, push.
2. Descarga el nuevo `.msix` (versión `1.2.0.0`; la Store reserva el 4.º número en 0 y la versión debe ser mayor que la anterior).
3. Partner Center → **Actualización** del envío → sube el paquete → certificación. Los usuarios reciben la actualización automática desde la Store.

## 6. Notas técnicas
- Paquete: x64, `Windows.Desktop` ≥ 10.0.17763.0, capacidad `runFullTrust`, alias de ejecución `PDFFacil.exe`.
- Datos: `QSettings` (registro HKCU) se virtualiza dentro del contenedor; los PDF se leen/escriben donde el usuario elige (fuera de AppData no se redirige). Las claves del ajuste de la versión Inno **no** migran al MSIX (solo se pierde la última carpeta/geometría).
- Instalar MSIX y Inno a la vez es posible; son apps distintas para Windows.
- La identidad de la Store es independiente de `AppId` de Inno.
- Datos del editor: Hefesto2JS (autor Luis Mayta). `AppPublisher` de Inno ahora es `Hefesto2JS`, solo metadato.

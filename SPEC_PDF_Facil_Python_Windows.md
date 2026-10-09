# SPEC — PDF Fácil

**Versión:** 1.0 (MVP)  
**Plataforma de destino:** Windows 10/11 x64  
**Desarrollo:** Ubuntu Linux  
**Idioma de interfaz:** Español  
**Tipo:** Aplicación de escritorio 100 % offline

## 1. Objetivo

Crear una aplicación de escritorio simple y segura que permita unir múltiples PDF con nombres arbitrarios, definiendo su orden **sin renombrar archivos**. El público principal es una persona no técnica que realiza esta tarea habitualmente y quiere evitar servicios de pago.

### Resultado esperado

La usuaria abre **PDF Fácil**, arrastra varios PDF, cambia el orden visualmente, presiona **Unir PDF**, elige el destino y obtiene un único documento. Los originales nunca se modifican.

## 2. Stack y decisiones

- **Python 3.12+**.
- **PySide6 (Qt Widgets)** para UI de escritorio.
- **pypdf** como motor de combinación y lectura de metadatos/páginas.
- **PyMuPDF (opcional)** para renderizar miniaturas; encapsular detrás de una interfaz y revisar su licencia AGPL/comercial antes de distribución. Para MVP puede omitirse la previsualización y evitar esta dependencia.
- **PyInstaller** para empaquetado Windows.
- **pytest** + **pytest-qt** para pruebas.
- **GitHub Actions, `windows-latest`** para generar el ejecutable Windows. PyInstaller **no hace cross-compilation Linux → Windows**.
- Sin servidor, API, base de datos ni conexión obligatoria.

**Preferencia:** entregar inicialmente versión `onedir` en ZIP con `PDF_Facil.exe`; evaluar `onefile` después de probar arranque, falsas alarmas de antivirus y estabilidad. El ejecutable se construye en Windows.

## 3. Alcance MVP (obligatorio)

### 3.1 Importación

- Botón **Agregar PDF** con selección múltiple.
- Drag & drop de archivos desde Explorador de Windows.
- Botón **Agregar carpeta** que incorpore PDFs de la carpeta seleccionada (solo nivel actual en MVP; no recursivo).
- Validación por contenido y lectura real, no solo por extensión.
- Si un documento está dañado o cifrado, mostrar mensaje individual y permitir continuar con otros.
- Si un PDF requiere contraseña, solicitarla de forma temporal y no almacenarla.
- Admisión de nombres Unicode, rutas con espacios y nombres duplicados en distintas carpetas.
- Si el mismo archivo se agrega dos veces, preguntar si se desea mantener duplicado (caso válido).

### 3.2 Lista y orden

- Tabla/lista central: posición, nombre, páginas, tamaño, ruta (tooltip), estado.
- Reordenar mediante arrastrar y soltar dentro de la lista.
- Botones **Subir**, **Bajar**, **Quitar**, **Vaciar lista**.
- Soporte para selección múltiple al quitar.
- Numeración visible actualizada automáticamente.
- El orden visible es la fuente de verdad para generar el PDF; **nunca** ordenar automáticamente por nombre al fusionar.
- Cuando se importe una carpeta, ordenar alfabéticamente solo el lote nuevo como punto de partida, sin alterar el orden manual existente.

### 3.3 Unión

- Botón principal **Unir PDF**.
- Cuadro de diálogo para guardar con nombre por defecto `Documento_unido.pdf` y última carpeta utilizada.
- Confirmar antes de sobrescribir cualquier archivo de salida.
- Impedir que el destino sea igual a la ruta de cualquiera de los originales.
- Ejecutar en worker/thread con señales Qt para que la interfaz no se congele.
- Mostrar estado de progreso: preparación, archivo actual, finalización.
- Escribir a archivo temporal **en la misma carpeta de destino** y mover/reemplazar de forma atómica al completar cuando lo soporte el sistema de archivos.
- Ante error o cancelación, retirar el temporal y conservar originales y versión anterior del destino.
- Verificar al final que el PDF resultante se pueda abrir y tenga el número esperado de páginas.
- Mensaje de éxito con acciones **Abrir archivo** y **Abrir carpeta**.
- No imprimir contenido de los documentos en logs.

### 3.4 Usabilidad

- Interfaz 100 % español; sin cuentas ni pantallas de bienvenida.
- Ventana única con área de arrastre, lista de archivos y botón de unión claro.
- Teclas accesibles para operaciones principales; tabulación coherente.
- Indicador `N archivos · M páginas`.
- Guardar configuración no sensible (última carpeta, geometría de ventana) con `QSettings`.
- Permitir cerrar con confirmación mientras una unión esté en marcha.

## 4. Opciones para fase 1.1 (no bloquear MVP)

- Miniaturas/previsualización de primera página usando un renderer compatible con la licencia elegida.
- Selección de rango por archivo (`1-3,5,7-9`) con validación y contador de páginas efectivas.
- Guardar/abrir proyectos de orden (`.json`) con rutas y verificación de disponibilidad.
- Plantillas de expedientes (solicitud → identificación → anexos).
- Rotación de páginas, eliminación de páginas, compresión y marcador/índice.
- Modo oscuro y actualización manual por descarga.

**No implementar OCR, edición de texto, firma electrónica, nube o sincronización en el MVP.**

## 5. Maqueta de interfaz

```text
┌────────────────────────────────────────────────────────────────┐
│ PDF Fácil                                     [—] [□] [X]     │
├────────────────────────────────────────────────────────────────┤
│   Suelta aquí tus PDF    [Agregar PDF] [Agregar carpeta]       │
├────┬───────────────────────┬─────────┬─────────┬───────────────┤
│ #  │ Documento             │ Páginas │ Tamaño  │ Estado        │
├────┼───────────────────────┼─────────┼─────────┼───────────────┤
│ 1  │ Solicitud.pdf         │ 2       │ 230 KB  │ Listo         │
│ 2  │ Identidad.pdf         │ 1       │ 900 KB  │ Listo         │
│ 3  │ Anexos.pdf            │ 7       │ 1.8 MB  │ Listo         │
├────┴───────────────────────┴─────────┴─────────┴───────────────┤
│ [Subir] [Bajar] [Quitar] [Vaciar lista]                        │
├────────────────────────────────────────────────────────────────┤
│ 3 archivos · 10 páginas                     [ UNIR PDF ]        │
└────────────────────────────────────────────────────────────────┘
```

## 6. Modelo y arquitectura

### Entidad `PdfItem`

- `id`: UUID interno único.
- `path`: `pathlib.Path` absoluto.
- `display_name`: nombre visible.
- `page_count`: número entero positivo.
- `size_bytes`: tamaño del archivo.
- `is_encrypted`: booleano.
- `password`: nunca persistir; solo en memoria temporal si es imprescindible.
- `status`: ready/error.

### Carpetas

```text
pdf-facil/
├── app/
│   ├── main.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── pdf_list_model.py
│   │   └── widgets/
│   ├── core/
│   │   ├── pdf_inspector.py
│   │   ├── pdf_merger.py
│   │   └── pdf_validator.py
│   ├── services/
│   │   ├── file_service.py
│   │   ├── settings_service.py
│   │   └── merge_worker.py
│   └── models/
│       └── pdf_item.py
├── tests/
│   ├── test_merge.py
│   ├── test_order.py
│   ├── test_validation.py
│   └── test_ui.py
├── assets/
├── .github/workflows/build-windows.yml
├── pyproject.toml
├── requirements.lock
├── README.md
└── LICENSE
```

Mantener la lógica de unión independiente de Qt, probada con archivos de ejemplo generados durante los tests. La UI nunca debe decidir ni alterar silenciosamente el orden de los documentos.

## 7. Algoritmo de unión

1. Tomar una copia inmutable de la lista ordenada al momento de pulsar **Unir PDF**.
2. Validar lista no vacía, rutas existentes, posibilidad de lectura, contraseña si aplica y destino seguro.
3. Calcular el total previsto de páginas.
4. Preparar archivo temporal en la carpeta del destino.
5. Recorrer ítems en **orden visual**, anexando todas sus páginas con `pypdf.PdfWriter` (o subconjuntos cuando fase 1.1 los habilite).
6. Reportar progreso desde el worker usando señales, sin modificar widgets directamente desde otro hilo.
7. Grabar y cerrar correctamente los objetos de escritura.
8. Comprobar apertura y conteo del archivo temporal.
9. Publicar archivo final sin corromper uno anterior ante fallos.
10. Borrar el temporal en rutas de error/cancelación y limpiar recursos.

**Nota:** algunos PDF problemáticos, con formularios, firmas digitales, enlaces, anotaciones o estructura no estándar pueden perder propiedades o invalidar firmas al fusionarse. Avisar antes de la unión si se detecta firma digital; no prometer preservación de firma.

## 8. Seguridad y manejo de errores

- Los PDF se procesan localmente; ninguna subida a terceros.
- No ejecutar código, scripts, adjuntos ni acciones embebidas de los PDF.
- Tratar archivos de entrada como datos no confiables.
- Capturar errores por archivo con mensajes comprensibles sin bloquear toda la sesión.
- No persistir contraseñas ni extraer información sensible en logs.
- El procesamiento de un archivo malicioso no tiene aislamiento fuerte por ejecutarse localmente: usar bibliotecas actualizadas y límites razonables de recursos cuando sea posible.
- Eliminar correctamente temporales tras fallos; evitar sobrescribir las entradas.

## 9. Distribución y SmartScreen

- Compilar desde GitHub Actions en Windows con versiones de dependencias fijadas.
- Publicar ZIP de distribución `PDF_Facil-Windows-x64.zip`, con directorio completo `onedir` y el ejecutable `PDF_Facil.exe`.
- Añadir `icon.ico`, metadatos de versión, empresa/nombre del producto y README breve.
- Entregar inicialmente un **ZIP portable**, sin instalador, para reducir complejidad.
- Opcional: construir un instalador por usuario con Inno Setup en versión posterior.
- **SmartScreen:** un `.exe` nuevo y sin firma puede mostrar “editor desconocido”/advertencia de reputación. No desactivar Defender/SmartScreen, ni usar trucos de evasión; documentar instalación y verificación del origen.
- Firma digital comercial opcional para distribución más amplia; firmar no garantiza ausencia inmediata de advertencias de reputación.
- Para el equipo de la esposa, instalación y revisión inicial asistida; después usar acceso directo al ejecutable instalado.
- Documentar checksum SHA-256 del ZIP publicado.

### Workflow Windows

El agente debe crear `.github/workflows/build-windows.yml` que:

1. Se active manualmente (`workflow_dispatch`) y en tags `v*`.
2. Use runner Windows.
3. Configure Python compatible.
4. Instale dependencias fijadas.
5. Ejecute pytest.
6. Genere el `onedir` con PyInstaller (`--windowed`, nombre `PDF_Facil`, ícono opcional).
7. Compruebe presencia del ejecutable y dependencias.
8. Cree ZIP y publique como artifact de Actions.
9. Registre checksum SHA-256.

## 10. Pruebas de aceptación obligatorias

| ID | Escenario | Resultado esperado |
|---|---|---|
| A01 | Unir tres PDF con nombres arbitrarios | PDF final respeta orden manual |
| A02 | Cambiar orden 3→1 | Primera página corresponde al nuevo primer PDF |
| A03 | Agregar dos archivos llamados igual desde carpetas distintas | Ambos se distinguen y pueden unirse |
| A04 | Agregar 100 PDF pequeños | Aplicación conserva capacidad de respuesta |
| A05 | Seleccionar PDF corrupto | Error claro; otros documentos permanecen disponibles |
| A06 | Seleccionar PDF con contraseña | Solicita contraseña; no la guarda |
| A07 | Elegir destino igual al archivo original | Operación bloqueada |
| A08 | Intentar sobrescribir salida existente | Pide confirmación |
| A09 | Falla de escritura por permisos/disco | Originales y salida previa intactos |
| A10 | Documentos con tildes, ñ y caracteres Unicode | Se abren y guardan correctamente |
| A11 | Fusionar mientras se interactúa con ventana | La interfaz no se bloquea |
| A12 | Abrir resultado | Se abre con visor PDF por defecto |
| A13 | Agregar mismo archivo dos veces intencionalmente | Ambas copias se incluyen tras confirmación |
| A14 | Cancelar durante procesamiento | No queda un archivo de salida incompleto |

Pruebas de integración con archivos sintéticos que incluyan páginas con texto identificable para verificar su orden real, no solo el número total de páginas.

## 11. Criterios de definición de terminado (DoD)

- El flujo principal completo funciona offline en Windows 10/11 x64.
- Se pueden agregar, quitar y reordenar PDF sin renombrarlos.
- Ningún original es modificado.
- Compilación reproducible en runner Windows.
- Tests automatizados pasan.
- Se genera ZIP portable ejecutable y manual de una página.
- Los errores habituales se muestran en español sin stack traces en la interfaz.
- Se documenta el comportamiento de SmartScreen honestamente.

## 12. Instrucciones directas al agente

> Implementa el MVP de **PDF Fácil** según este SPEC. Prioriza flujo claro, estabilidad, seguridad de archivos y calidad de pruebas sobre funciones decorativas. No añadas backend, telemetría ni servicios online. No cambies el stack sin justificación. Construye una interfaz Qt Widgets sencilla y coherente; la lista debe ser reordenable arrastrando y mediante botones. Proporciona instrucciones de ejecución en Ubuntu, tests y workflow listo para generar ZIP portable de Windows. No asegures que el ejecutable jamás activará SmartScreen. Entrega código funcional y un README para la usuaria final.

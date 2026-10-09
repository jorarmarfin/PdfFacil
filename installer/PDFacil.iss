; Instalador de PDFácil (Inno Setup 6). Empaqueta dist\PDF_Facil (PyInstaller --onedir).
; Compilar: ISCC /DAppVersion=1.0.0 installer\PDFacil.iss
; Los ajustes del usuario viven en QSettings (registro HKCU\Software\PDFFacil): ni
; actualizar ni desinstalar los toca.

#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif
#define AppName "PDFácil"
#define AppDirName "PDFacil"
#define AppExe "PDF_Facil.exe"
#define AppPublisher "PDF Fácil"
#define SourceDir "..\dist\PDF_Facil"

[Setup]
; GUID fijo: identifica la app para actualizar sobre versiones previas. No cambiar.
AppId={{6F0B7C1E-3A52-4D8B-9E47-5C2A1D90B3F8}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador de {#AppName}
; Instalación por usuario (sin admin) por defecto: %LOCALAPPDATA%\Programs\PDFácil
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\{#AppDirName}
DefaultGroupName={#AppDirName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\LICENSE
OutputDir=..\installer_output
OutputBaseFilename=PDFacil-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Cierra la app si está abierta durante una actualización y la reabre después.
CloseApplications=yes
RestartApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

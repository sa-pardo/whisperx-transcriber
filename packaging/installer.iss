; WhisperX Transcriber — Inno Setup Installer Script
;
; Strategy: thin installer (~20-25 MB).
;   - Installs only the launcher exe and source files.
;   - NO torch, NO whisperx, NO model weights bundled.
;   - On first launch, the app's built-in setup wizard downloads
;     the AI backend (~700 MB CPU / ~3 GB GPU) into {app}\runtime\.
;
; Build requirements:
;   1. Run packaging\build.bat first to produce dist\WhisperX Transcriber\
;   2. Run: ISCC packaging\installer.iss
;      (or open this file in Inno Setup Compiler and press Build)
;
; Output: dist\installer\WhisperX-Transcriber-Setup-v{version}.exe

#define AppName      "WhisperX Transcriber"
#define AppVersion   "1.0.0"
#define AppPublisher "Muqaddimah"
#define AppURL       "https://github.com/ibrahimqureshae/whisperx-transcriber"
#define AppExeName   "WhisperX Transcriber.exe"
#define AppID        "{A3C7D8E9-4B2F-4A1D-9C3E-12AB34CD56EF}"

[Setup]
; Unique GUID — do NOT change after first release (used for update detection)
AppId={#AppID}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Install per-user to %LOCALAPPDATA%\Programs — no admin / no UAC prompt
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; 64-bit only (torch does not ship 32-bit Windows wheels)
ArchitecturesInstallIn64BitMode=x64

; Output
OutputDir=..\dist\installer
OutputBaseFilename=WhisperX-Transcriber-Setup-v{#AppVersion}

; Appearance
SetupIconFile=..\assets\icon.ico
WizardStyle=modern
WizardSmallImageFile=..\assets\icon.ico

; Compression — LZMA ultra gives the smallest installer
Compression=lzma2/ultra64
SolidCompression=yes

; Misc
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#AppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
  Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; \
  Flags: unchecked

[Files]
; Thin launcher and all its bundled GUI deps (_internal/).
; runtime\ and Models\ are intentionally empty — filled on first run.
Source: "..\dist\WhisperX Transcriber\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Exclude the placeholder empty dirs from the recursive copy above —
; Inno Setup will create them fresh via [Dirs] below.
; (The above Source already copies them since they exist in dist)

[Dirs]
; Ensure runtime\ and Models\ exist with write permissions for the user.
Name: "{app}\runtime"
Name: "{app}\Models"

[Icons]
; Start Menu
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Desktop (optional task)
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; \
  Tasks: desktopicon

[Run]
; Offer to launch after install
Filename: "{app}\{#AppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the runtime venv and model cache created by the app.
; These are not tracked by the installer so must be explicitly listed.
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\Models"

[Messages]
; Friendly description shown in Add/Remove Programs
BeveledLabel=WhisperX AI Transcription

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nThe installer is small (~25 MB). The AI engine (~700 MB) downloads automatically on first launch.%n%nClick Next to continue.

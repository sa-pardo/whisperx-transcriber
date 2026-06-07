; WhisperX Transcriber — Inno Setup Installer Script
;
; Thin installer (~25 MB). Drops the launcher + source files only.
; NO torch, NO whisperx, NO model weights bundled.
; The AI backend downloads on first launch via the setup wizard.
;
; Build:
;   1. packaging\build.bat   (builds launcher + stages files)
;   2. ISCC packaging\installer.iss   (or build.bat runs this automatically)
;
; Output: dist\installer\WhisperXTranscriber-Setup.exe

#define AppName       "WhisperX Transcriber"
#define AppFolderName "WhisperXTranscriber"
#define AppVersion    "1.0.0"
#define AppPublisher  "Muqaddimah"
#define AppURL        "https://github.com/ibrahimqureshae/whisperx-transcriber"
#define AppExeName    "WhisperXTranscriber.exe"
[Setup]
AppId={{A3C7D8E9-4B2F-4A1D-9C3E-12AB34CD56EF}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Install per-user — no admin / no UAC prompt
DefaultDirName={localappdata}\Programs\{#AppFolderName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=yes

; 64-bit only
ArchitecturesInstallIn64BitMode=x64

; Output
OutputDir=..\dist\installer
OutputBaseFilename=WhisperXTranscriber-Setup

; Appearance
SetupIconFile=..\assets\icon.ico
WizardStyle=modern

; Compression
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
  GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\WhisperXTranscriber\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\runtime"
Name: "{app}\Models"

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; \
  Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\runtime"
Type: filesandordirs; Name: "{app}\Models"

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nThe installer is small (~25 MB). The AI engine (~700 MB) downloads automatically on first launch.%n%nClick Next to continue.

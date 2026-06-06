# Packaging Guide

For maintainers and contributors who want to build the Windows installer.

---

## How the installer works

```
WhisperXTranscriber-Setup.exe  (~25 MB download)
│
│  installs to %LOCALAPPDATA%\Programs\WhisperXTranscriber\
│
├── WhisperXTranscriber.exe    ← thin launcher (PyInstaller, GUI only)
├── app.py                     ← main app (source)
├── setup_wizard.py            ← first-run wizard (source)
├── assets/
├── runtime/                   ← empty on install, filled on first launch
└── Models/                    ← empty on install, filled on first transcription
```

The installer ships **no AI models, no PyTorch, no whisperx**.  
Everything downloads on first launch via the setup wizard.

---

## Prerequisites

| Tool | Version | Link |
|---|---|---|
| Python | 3.10–3.13 | [python.org](https://www.python.org/downloads/) |
| Inno Setup | 6.x | [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php) |
| UPX *(optional)* | any | [upx.github.io](https://upx.github.io/) — reduces launcher size by ~30% |

---

## Build steps

### 1 — Set up the dev environment (once)

```batch
run.bat
```

This creates `.venv` with all dependencies. Required before building — PyInstaller needs the packages present to bundle the launcher.

### 2 — Build

```batch
packaging\build.bat
```

What it does:
1. Checks `.venv` exists (exits with error if not)
2. Installs `pyinstaller` into `.venv` if missing
3. Runs PyInstaller with `packaging/launcher.spec` — produces a thin launcher (~30 MB) with **no torch, no whisperx, no ML packages**
4. Copies `app.py`, `setup_wizard.py`, `version.txt`, and `requirements-*.txt` into `dist/WhisperXTranscriber/`
5. Creates empty `runtime/` and `Models/` placeholder directories
6. Auto-runs `ISCC.exe` if Inno Setup 6 is found on the system

### 3 — Run Inno Setup manually (if not auto-run)

```batch
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
```

Or open `packaging/installer.iss` in the Inno Setup Compiler GUI and press **Build**.

---

## Output

```
dist/
├── WhisperXTranscriber/              ← PyInstaller onedir (test this directly)
│   ├── WhisperXTranscriber.exe
│   ├── _internal/                    ← Python + customtkinter + Pillow only
│   ├── app.py
│   ├── setup_wizard.py
│   ├── version.txt
│   ├── assets/
│   ├── runtime/                      ← empty placeholder
│   └── Models/                       ← empty placeholder
│
└── installer/
    └── WhisperXTranscriber-Setup.exe ← ship this
```

---

## What is and isn't bundled

### Inside the installer (~25 MB)

| Included | Size |
|---|---|
| Python runtime (slim) | ~15 MB |
| customtkinter | ~5 MB |
| Pillow | ~4 MB |
| app.py, setup_wizard.py, assets | ~1 MB |

### Downloaded on first launch (not bundled)

| Package | Size | Notes |
|---|---|---|
| torch + torchaudio (CPU) | ~700 MB | User chooses CPU or GPU |
| torch + torchaudio (CUDA 12.1) | ~3 GB | Only if NVIDIA GPU detected |
| whisperx | ~18 MB | Installed after torch |
| faster-whisper + ctranslate2 | ~80 MB | Core inference engine |
| customtkinter, Pillow | ~9 MB | Installed into runtime/ venv |
| Models (large-v2) | ~3 GB | Downloaded on first transcription |

---

## Installer settings

Key settings in `packaging/installer.iss`:

| Setting | Value |
|---|---|
| `DefaultDirName` | `{localappdata}\Programs\WhisperXTranscriber` |
| `PrivilegesRequired` | `lowest` — no UAC prompt |
| `Compression` | `lzma2/ultra64` — maximum compression |
| Uninstall | Removes `runtime/` and `Models/` on uninstall |

---

## Release checklist

Before tagging a new release:

- [ ] Update `version.txt` (root of repo) — this is what the in-app update check reads from GitHub
- [ ] Update `#define AppVersion` in `packaging/installer.iss`
- [ ] Delete `dist/` and run `packaging\build.bat` clean
- [ ] Test `dist/WhisperXTranscriber/WhisperXTranscriber.exe` directly before building installer
- [ ] Test installer on a clean machine (no Python pre-installed if possible)
- [ ] Test with NVIDIA GPU (verify GPU is detected in wizard step 2)
- [ ] Test uninstall — confirm `runtime/` and `Models/` are removed
- [ ] Upload `dist/installer/WhisperXTranscriber-Setup.exe` to the GitHub release
- [ ] Tag the release: `git tag v1.0.0 && git push --tags`

---

## Version bump (quick reference)

Two files to update per release:

```
version.txt                        ← plain version string, e.g. 1.0.1
packaging/installer.iss            ← #define AppVersion "1.0.1"
```

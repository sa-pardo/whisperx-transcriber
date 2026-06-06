# WhisperX Transcriber

> A clean Windows desktop GUI for AI-powered transcription with word-level timestamps.  
> Built on [WhisperX](https://github.com/m-bain/whisperX) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

![App Screenshot](assets/screenshot.png)

---

## What it does

- Transcribes audio and video files with **word-level timestamps**
- Exports to **SRT, VTT, TXT, TSV, JSON, or Word JSON**
- Auto-detects your **GPU** (NVIDIA CUDA) or falls back to CPU
- Clean GUI — no terminal needed for end users
- Small download — AI models are **never bundled**, they download on first use

---

## Who is this for?

- **End users** — download the installer, click through setup, start transcribing
- **Developers** — clone the repo, run one script, everything installs automatically

Pick your path below.

---

---

# 👤 For End Users

> No Python, no terminal, no technical knowledge required.

### Step 1 — Download the installer

Go to the [**Releases**](../../releases) tab and download:

```
WhisperXTranscriber-Setup.exe
```

The installer is small (~25 MB). The AI engine downloads separately on first launch.

### Step 2 — Run the installer

- Double-click `WhisperXTranscriber-Setup.exe`
- **No admin password required** — installs to your user profile
- A Start Menu shortcut and optional Desktop shortcut are created

### Step 3 — First launch (one-time setup)

On first launch, the **Setup Wizard** opens automatically:

```
┌──────────────────────────────────────────────┐
│   WhisperX Transcriber — First-time Setup    │
│                                              │
│   Step 1: Welcome — what will be downloaded  │
│   Step 2: GPU check — NVIDIA or CPU mode     │
│   Step 3: Installing — live progress log     │
│   Step 4: Done — Launch App                  │
└──────────────────────────────────────────────┘
```

The wizard:
1. Checks if Python 3.10+ is installed (required — see note below)
2. Detects your GPU automatically
3. Downloads and installs the AI engine (~700 MB CPU or ~3 GB GPU)
4. Every future launch opens instantly — setup only runs once

> **Python is required.** The wizard will prompt you if it's missing.  
> Install from [python.org](https://www.python.org/downloads/) — tick **"Add Python to PATH"** during install.

### Step 4 — Transcribe

1. Drop an audio or video file into the app
2. Choose your model and output format
3. Click **Run**

### CPU vs GPU

| | CPU | GPU |
|---|---|---|
| First-run download | ~700 MB | ~3 GB |
| Transcription speed | ~0.5× realtime | ~8–15× realtime |
| Hardware required | Any Windows PC | NVIDIA GPU + driver 525+ |

The wizard detects your GPU and selects the right mode automatically. You can override it.

### Models

Models download on first transcription — never bundled in the installer.

| Model | Size | Best for |
|---|---|---|
| `tiny` | ~75 MB | Quick preview |
| `base` | ~145 MB | Fast drafts |
| `small` | ~465 MB | Good balance |
| `medium` | ~1.5 GB | High accuracy |
| `large-v2` *(default)* | ~3 GB | Best quality |
| `large-v3` | ~3 GB | Latest |

### Output formats

| Format | Description |
|---|---|
| `word_json` | Per-word `{word, start, end, score}` — for developers |
| `srt` | Standard subtitles (works in VLC, YouTube, etc.) |
| `vtt` | WebVTT subtitles |
| `txt` | Plain text transcript |
| `tsv` | Tab-separated with timestamps |
| `json` | Full segment JSON |

### Troubleshooting

**"Python not found"** — Install [Python 3.10+](https://www.python.org/downloads/) and tick "Add Python to PATH".

**Setup wizard fails mid-download** — Click **Retry**. It cleans up and starts fresh.

**CUDA out of memory** — Lower the Batch Size in the Model panel (try 4 or 8).

**Alignment fails** — Disable word alignment in the Output panel. SRT/VTT still export.

**Anything else** — Open a [GitHub issue](../../issues) and paste the log output.

---

---

# 🛠️ For Developers

> Clone, run one script, and you're in.

### Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Git
- Windows (Linux/macOS supported via `run.sh`, GUI features may vary)
- NVIDIA GPU recommended but not required

### Quick start

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat          # Windows
# or
bash run.sh      # macOS / Linux
```

`run.bat` / `run.sh` does everything on first run:
1. Creates a `.venv` virtual environment
2. Detects your GPU and installs the right PyTorch build
3. Installs WhisperX and all UI dependencies
4. Launches the app

**Every subsequent run opens the app instantly** — setup is skipped once `.venv` exists.

### Project structure

```
whisperx-transcriber/
│
├── app.py                  Main GUI application
├── launcher.py             Thin entry point used by the packaged .exe
├── setup_wizard.py         First-run wizard (used by launcher.exe, not run.bat)
├── transcribe.py           Headless CLI tool
│
├── run.bat                 Windows developer launcher
├── run.sh                  macOS / Linux developer launcher
│
├── requirements-cpu.txt    PyTorch CPU wheels
├── requirements-gpu.txt    PyTorch CUDA 12.1 wheels
├── requirements-core.txt   whisperx, customtkinter, Pillow
├── requirements-build.txt  Build tools (pyinstaller)
│
├── packaging/
│   ├── build.bat           Builds the thin launcher exe + runs Inno Setup
│   ├── launcher.spec       PyInstaller spec — GUI only, no ML packages
│   └── installer.iss       Inno Setup script — produces the .exe installer
│
└── assets/
    └── screenshot.png      App screenshot for README
```

### Manual install (without run.bat)

```bash
python -m venv .venv

# GPU (NVIDIA)
.venv\Scripts\pip install -r requirements-gpu.txt
# CPU only
.venv\Scripts\pip install -r requirements-cpu.txt

# Then install the app dependencies
.venv\Scripts\pip install -r requirements-core.txt

# Launch
.venv\Scripts\python app.py
```

### CLI usage (transcribe.py)

For scripting or batch processing without the GUI:

```bash
python transcribe.py audio.mp3
python transcribe.py audio.mp3 --language en --model large-v2
python transcribe.py audio.mp3 --device cpu --output srt
python transcribe.py audio.mp3 --model-dir /path/to/models
```

Options:

```
--model       tiny, base, small, medium, large-v2, large-v3  (default: large-v2)
--language    en, ar, fr, de, es, zh, ja, ...               (default: auto-detect)
--device      cuda, cpu                                      (default: auto-detect)
--output      word_json, srt, vtt, txt, tsv, json           (default: word_json)
--model-dir   path to model cache                           (default: ./Models)
```

### Building the installer

See [PACKAGING.md](PACKAGING.md) for the full guide. Quick version:

```bash
# 1. Build the thin launcher exe (requires .venv to exist)
packaging\build.bat

# 2. Build the installer (requires Inno Setup 6)
# build.bat runs this automatically if ISCC.exe is found
# Otherwise: download from https://jrsoftware.org/isdl.php
```

Output: `dist/installer/WhisperXTranscriber-Setup.exe`

---

---

## Tech stack

| Layer | Library |
|---|---|
| GUI | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Transcription | [WhisperX](https://github.com/m-bain/whisperX) |
| ASR backend | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| Inference runtime | [CTranslate2](https://github.com/OpenNMT/CTranslate2) |
| Packaging | [PyInstaller](https://pyinstaller.org/) + [Inno Setup 6](https://jrsoftware.org/isinfo.php) |

## Roadmap

- [ ] Speaker diarization UI
- [ ] Batch folder transcription
- [ ] Drag-and-drop file input
- [ ] macOS `.app` bundle
- [ ] Translation mode

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

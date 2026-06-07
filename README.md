# WhisperX Transcriber

> A clean Windows desktop app for AI-powered audio and video transcription.  
> Word-level timestamps. Works completely offline. No subscription. No cloud.

Built on [WhisperX](https://github.com/m-bain/whisperX) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — the fastest open-source speech recognition stack available.

---

## Why use this?

Most transcription tools are either expensive cloud services that send your audio to someone else's server, or complex Python scripts that require technical setup. WhisperX Transcriber is neither.

- **Your audio never leaves your machine.** Everything runs locally — no cloud, no API key, no subscription.
- **One-time setup, then works forever offline.** The AI engine downloads once (~1–3 GB). After that, you never need the internet again.
- **No terminal, no Python knowledge required** for end users. Extract the zip, run the exe, click through a one-time setup wizard. Done.
- **Fast.** On a modern NVIDIA GPU, it transcribes faster than realtime. Even on CPU it's practical for short and medium recordings.
- **Accurate.** Powered by OpenAI's Whisper large-v2 model — one of the best open-source speech recognition models available.
- **Word-level timestamps.** Every word is timestamped precisely, not just sentence segments. Essential for subtitle work, content search, and downstream processing.

---

## What it does

- Transcribes **audio and video files** to text with word-level timestamps
- Exports to **SRT, VTT, TXT, TSV, JSON**, or a custom **Word JSON** format
- Supports **17 languages** in the GUI, **99 languages** via the CLI
- Auto-detects your **NVIDIA GPU** for fast transcription, falls back to CPU automatically
- Strips silence automatically with a built-in **VAD (Voice Activity Detection)** filter
- Produces **karaoke-style highlighted subtitles** (word-by-word highlighting in SRT/VTT)
- Runs **100% offline** after the one-time first-run setup

---

## One-time download — works offline forever

The app is designed around a simple idea: **download once, use forever**.

```
First launch (internet required, one time only)
  └── Setup Wizard downloads the AI engine: torch + whisperX (~1–3 GB)
      └── Saved to runtime/ folder next to the app
          └── Every launch after this: no internet needed, opens instantly
```

The AI **models** (e.g. large-v2) also download once on first use and are cached locally. After that, transcription works with zero internet connection — even on a plane.

---

## Supported languages

The GUI exposes **17 languages** with a dropdown:

| Language | Code | Language | Code |
|---|---|---|---|
| English | `en` | Russian | `ru` |
| Arabic | `ar` | Portuguese | `pt` |
| French | `fr` | Italian | `it` |
| German | `de` | Dutch | `nl` |
| Spanish | `es` | Polish | `pl` |
| Chinese | `zh` | Turkish | `tr` |
| Japanese | `ja` | Persian | `fa` |
| Korean | `ko` | Urdu | `ur` |
| Hindi | `hi` | | |

The **Auto-detect** option lets Whisper identify the language automatically — useful when you're not sure or the audio contains multiple languages.

The underlying Whisper model supports **99 languages** in total. The full list is accessible via the CLI (`transcribe.py`) using any [ISO 639-1 language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

---

## Who is this for?

- **Journalists and researchers** — transcribe interviews and lectures quickly, with accurate timestamps
- **Content creators** — generate subtitles for videos in minutes instead of hours
- **Translators** — get a timestamped base transcript before translating
- **Students** — transcribe lectures, seminars, and recorded classes
- **Anyone who handles audio in Arabic, Urdu, Persian, or other non-Latin-script languages** — Whisper handles right-to-left scripts natively
- **Privacy-conscious users** — nothing is uploaded anywhere, ever

---

---

# For End Users

> No terminal, no technical knowledge required.

### Step 1 — Download

Go to the [**Releases**](../../releases) tab and download:

```
WhisperXTranscriber.zip
```

The zip is ~19 MB. The AI engine downloads separately on first launch.

### Step 2 — Extract and run

- Extract the zip anywhere (e.g. `C:\Apps\WhisperXTranscriber\`)
- Double-click `WhisperXTranscriber.exe`
- **No installer, no admin rights required** — fully portable

### Step 3 — First launch (one-time setup, internet required)

On first launch, the **Setup Wizard** opens automatically:

1. **Welcome** — shows what will be downloaded and your GPU status
2. **Begin Setup** — downloads the AI engine (1–3 GB, takes 5–30 min depending on connection)
3. **Done** — click Launch. Every future launch opens instantly with no setup

> **Python 3.10+ is required** for the setup wizard to install the AI engine.  
> The wizard will tell you if it's missing — install from [python.org](https://www.python.org/downloads/) and tick **"Add Python to PATH"**.  
> After setup is complete, Python is only used internally — you don't need to touch it again.

### Step 4 — Transcribe

1. Click **Files** and select your audio or video file
2. Go to **Model** to choose model size and device
3. Go to **Output** to choose your export formats
4. Click **Run**

The status bar shows each phase: Downloading model → Loading model → Loading audio → Transcribing → Aligning → Saving → Done.

---

### CPU vs GPU

| | CPU | GPU |
|---|---|---|
| Setup download | ~1 GB | ~2–3 GB |
| Transcription speed | ~0.3–0.5× realtime | ~8–15× realtime |
| Hardware required | Any Windows PC | NVIDIA GPU + driver 525+ |

The wizard detects your GPU automatically. You can override the device in the **Model** panel.

---

### Models

Models download on first use and are cached locally — never re-downloaded.

| Model | Download size | Best for |
|---|---|---|
| `tiny` | ~75 MB | Quick preview, low accuracy |
| `base` | ~145 MB | Fast drafts |
| `small` | ~465 MB | Good balance of speed and accuracy |
| `medium` | ~1.5 GB | High accuracy |
| `large-v2` *(default)* | ~3 GB | Best quality, recommended |
| `large-v3` | ~3 GB | Latest version of large |

Start with `large-v2` unless you need faster results or have limited disk space.

---

### Output formats

| Format | Description |
|---|---|
| `word_json` | Per-word `{word, start, end, score}` — for developers and downstream tools |
| `srt` | Standard subtitles — works in VLC, YouTube, Premiere, DaVinci Resolve |
| `vtt` | WebVTT subtitles — for web video players |
| `txt` | Plain text transcript — no timestamps |
| `tsv` | Tab-separated with start/end timestamps per segment |
| `json` | Full segment-level JSON with all metadata |

Multiple formats can be selected at once. All are saved to the same output folder.

---

### Troubleshooting

**"Python not found"** — Install [Python 3.10+](https://www.python.org/downloads/) and tick "Add Python to PATH". Then re-run the app.

**Setup fails mid-download** — Click **Retry**. The wizard resumes where it left off and skips already-installed packages.

**CUDA out of memory** — Lower Batch Size in the Model panel. Try 8, then 4.

**Alignment fails** — Disable word alignment in the Output panel. All other formats (SRT, VTT, TXT, etc.) still export without it.

**Transcription is slow on CPU** — Use a smaller model (`small` or `base`), or reduce Batch Size.

**Anything else** — Open a [GitHub issue](../../issues) and paste the log output (click **Log** in the sidebar).

---

---

# For Developers

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
2. Detects your GPU and installs the correct PyTorch build
3. Installs WhisperX and all UI dependencies
4. Launches the app

**Every subsequent run opens the app instantly** — setup is skipped once `.venv` exists.

### Project structure

```
whisperx-transcriber/
│
├── app.py                  Main GUI application
├── launcher.py             Thin entry point used by the packaged .exe
├── setup_wizard.py         First-run wizard (runs inside the packaged .exe)
├── transcribe.py           Headless CLI tool for scripting and batch use
│
├── run.bat                 Windows developer launcher
├── run.sh                  macOS / Linux developer launcher
│
├── requirements-cpu.txt    PyTorch CPU wheels
├── requirements-gpu.txt    PyTorch CUDA wheels
├── requirements-core.txt   whisperx, customtkinter, Pillow
├── requirements-build.txt  Build tools (pyinstaller)
│
├── packaging/
│   ├── build.bat           Builds the thin launcher exe + creates portable zip
│   └── launcher.spec       PyInstaller spec — GUI only, no ML packages
│
└── assets/
    └── icon.ico            App icon
```

### Architecture — thin launcher pattern

The packaged `.exe` is intentionally tiny (~19 MB) because it contains **no AI packages at all**:

```
WhisperXTranscriber.exe  (PyInstaller onedir)
  └── Python runtime
  └── customtkinter + Pillow  (GUI only)
  └── setup_wizard (frozen inside)
      └── On first run: pip-installs whisperx + torch into runtime/
          └── On all later runs: spawns runtime/python app.py
```

This avoids bundling gigabytes of ML libraries into the exe, and means updates to the AI engine don't require a new download of the whole app.

### Manual install (without run.bat)

```bash
python -m venv .venv

# GPU (NVIDIA)
.venv\Scripts\pip install -r requirements-gpu.txt
# CPU only
.venv\Scripts\pip install -r requirements-cpu.txt

# App dependencies
.venv\Scripts\pip install -r requirements-core.txt

# Launch
.venv\Scripts\python app.py
```

### CLI usage (transcribe.py)

For scripting, batch processing, or accessing all 99 supported languages:

```bash
python transcribe.py audio.mp3
python transcribe.py audio.mp3 --language ar --model large-v2
python transcribe.py audio.mp3 --device cpu --output srt
python transcribe.py audio.mp3 --model-dir D:\models
```

Options:

```
--model       tiny, base, small, medium, large-v2, large-v3  (default: large-v2)
--language    any ISO 639-1 code, e.g. en, ar, fr, ur, fa    (default: auto-detect)
--device      cuda, cpu                                       (default: auto-detect)
--output      word_json, srt, vtt, txt, tsv, json            (default: word_json)
--model-dir   path to model cache                            (default: ./Models)
```

### Building the release zip

See [PACKAGING.md](PACKAGING.md) for the full guide. Quick version:

```bash
# Requires .venv to exist (run run.bat once first)
packaging\build.bat
```

Output: `dist/release/WhisperXTranscriber.zip`

---

---

## Tech stack

| Layer | Library |
|---|---|
| GUI | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Transcription | [WhisperX](https://github.com/m-bain/whisperX) |
| ASR backend | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| Inference runtime | [CTranslate2](https://github.com/OpenNMT/CTranslate2) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

## Roadmap

- [ ] Drag-and-drop file input
- [ ] Batch folder transcription
- [ ] Speaker diarization UI
- [ ] Translation mode (transcribe + translate to English)
- [ ] macOS `.app` bundle

---

## Open source — contributions welcome

WhisperX Transcriber is free and open source under the MIT license. The source code is fully available and the project welcomes contributions of any kind.

**Ways to contribute:**

- **Bug reports** — open an [issue](../../issues) with the log output and steps to reproduce
- **Feature requests** — open an issue describing the use case
- **Code contributions** — fork the repo, make your changes, open a pull request
- **Language support** — add more languages to the `_lang_map` in `app.py`
- **Testing** — test on different hardware, GPUs, or audio types and report findings

**Getting started as a contributor:**

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat   # sets up the dev environment and launches the app
```

The codebase is intentionally small and readable — `app.py` is the entire GUI, `setup_wizard.py` is the first-run installer, `transcribe.py` is the headless CLI. No framework magic, no hidden complexity.

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

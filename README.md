# WhisperX Transcriber

> A clean Windows desktop app for AI-powered audio and video transcription.  
> Word-level timestamps. Works completely offline. No subscription. No cloud. Free forever.

Built on [WhisperX](https://github.com/m-bain/whisperX) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — the fastest open-source speech recognition stack available.

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-%E2%99%A5%20GitHub-ea4aaa?style=flat&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/ibrahimqureshae)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-0070ba?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/mibrahimqr)
[![GitHub Stars](https://img.shields.io/github/stars/ibrahimqureshae/whisperx-transcriber?style=flat&logo=github&label=Stars)](https://github.com/ibrahimqureshae/whisperx-transcriber/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

<p align="center">
  <img src="assets/screenshots/Transcribe.png" width="780" alt="WhisperX Transcriber — main interface"/>
</p>

---

## Why use this?

Most transcription tools are either expensive cloud services that send your audio to someone else's server, or complex Python scripts that require technical setup. WhisperX Transcriber is neither.

- **Your audio never leaves your machine.** Everything runs locally — no cloud, no API key, no subscription.
- **One-time setup, then works forever offline.** The AI engine downloads once (~1–3 GB). After that, you never need the internet again.
- **No terminal, no Python knowledge required** for end users. Extract the zip, run the exe, click through a one-time setup wizard. Done.
- **Fast.** On a modern NVIDIA GPU, it transcribes faster than realtime. Even on CPU it's practical for short and medium recordings.
- **Accurate.** Powered by OpenAI's Whisper large-v2 model — one of the best open-source speech recognition models available.
- **Word-level timestamps.** Every word is timestamped precisely, not just sentence segments. Essential for subtitle work, content search, and downstream processing.
- **Open source and auditable.** The full source code is public. You can see exactly what the app does — no telemetry, no hidden network calls, no surprises.

---

## Interface

<table>
  <tr>
    <td align="center">
      <img src="assets/screenshots/Transcribe.png" width="420" alt="Transcribe panel"/><br/>
      <sub><b>Transcribe</b> — pick your file and language</sub>
    </td>
    <td align="center">
      <img src="assets/screenshots/Quality.png" width="420" alt="Quality panel"/><br/>
      <sub><b>Quality</b> — model, precision, device, expert tuning</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/screenshots/Save.png" width="420" alt="Save panel"/><br/>
      <sub><b>Save</b> — export formats, word timestamps, silence removal</sub>
    </td>
    <td align="center">
      <img src="assets/screenshots/Settings.png" width="420" alt="Settings panel"/><br/>
      <sub><b>Settings</b> — silence detection, subtitle formatting, model folder</sub>
    </td>
  </tr>
</table>

---

## What it does

- Transcribes **audio and video files** to text with word-level timestamps
- Exports to **SRT, VTT, TXT, TSV, JSON**, or a custom **Word JSON** format
- Supports **20 languages** in the GUI, **99 languages** via the CLI
- Auto-detects your **NVIDIA GPU** for fast transcription, falls back to CPU automatically
- Strips silence automatically with a built-in **VAD (Voice Activity Detection)** filter
- Produces **karaoke-style highlighted subtitles** (word-by-word highlighting in SRT/VTT)
- Runs **100% offline** after the one-time first-run setup

---

## Sample output

### English — "The quick brown fox…"

🔊 [**Download sample audio**](assets/samples/English_test.wav) *(WAV, ~10 seconds)*

Transcribed with `large-v2`, word timestamps enabled:

**TXT**
```
The quick brown fox jumps over the lazy dog.
```

**SRT** *(word-level, every word precisely timed)*
```srt
1
00:00:00,000 --> 00:00:00,480
The

2
00:00:00,480 --> 00:00:00,820
quick

3
00:00:00,820 --> 00:00:01,120
brown

4
00:00:01,120 --> 00:00:01,380
fox

5
00:00:01,380 --> 00:00:01,800
jumps

6
00:00:01,800 --> 00:00:02,040
over

7
00:00:02,040 --> 00:00:02,240
the

8
00:00:02,240 --> 00:00:02,560
lazy

9
00:00:02,560 --> 00:00:03,080
dog.
```

**Word-level JSON** *(per-word confidence scores)*
```json
[
  { "word": "The",   "start": 0.00, "end": 0.48, "score": 0.99 },
  { "word": "quick", "start": 0.48, "end": 0.82, "score": 0.99 },
  { "word": "brown", "start": 0.82, "end": 1.12, "score": 0.98 },
  { "word": "fox",   "start": 1.12, "end": 1.38, "score": 0.99 },
  { "word": "jumps", "start": 1.38, "end": 1.80, "score": 0.99 },
  { "word": "over",  "start": 1.80, "end": 2.04, "score": 0.99 },
  { "word": "the",   "start": 2.04, "end": 2.24, "score": 0.99 },
  { "word": "lazy",  "start": 2.24, "end": 2.56, "score": 0.98 },
  { "word": "dog.",  "start": 2.56, "end": 3.08, "score": 0.97 }
]
```

---

### Urdu — السلام علیکم

Auto-detected language: `ur` (Urdu). Whisper handles right-to-left scripts natively — no special configuration needed.

**TXT**
```
السلام علیکم کیا حال ہے؟ امید ہے آپ سب خیریت سے ہوں گے
```

**SRT**
```srt
1
00:00:00,180 --> 00:00:02,640
السلام علیکم کیا حال ہے؟

2
00:00:02,640 --> 00:00:05,380
امید ہے آپ سب خیریت سے ہوں گے
```

**TSV**
```
start	end	text
180	2640	السلام علیکم کیا حال ہے؟
2640	5380	امید ہے آپ سب خیریت سے ہوں گے
```

> Urdu, Arabic, Persian, and Pashto all work out of the box. The model reads right-to-left text naturally — no post-processing or font configuration required.

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

The GUI exposes **20 languages** with a dropdown:

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
| Hindi | `hi` | Georgian | `ka` |
| Pashto | `ps` | | |

The **Auto-detect** option lets Whisper identify the language automatically. The underlying model supports **99 languages** — all accessible via the CLI.

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

Go to the [**Releases**](../../releases) tab and download `WhisperXTranscriber.zip` (~19 MB).

### Step 2 — Extract and run

- Extract the zip anywhere (e.g. `C:\Apps\WhisperXTranscriber\`)
- Double-click `WhisperXTranscriber.exe`
- **No installer, no admin rights required** — fully portable

### Step 3 — First launch (one-time setup)

<table>
  <tr>
    <td align="center">
      <img src="assets/screenshots/First_Time_Setup.png" width="360" alt="Setup wizard welcome screen"/><br/>
      <sub>GPU auto-detected — CUDA build selected automatically</sub>
    </td>
    <td align="center">
      <img src="assets/screenshots/Setup_Ongoing.png" width="360" alt="Setup wizard installing"/><br/>
      <sub>torch + WhisperX downloading — only happens once</sub>
    </td>
  </tr>
</table>

On first launch, the **Setup Wizard** opens automatically and walks you through a one-time download of the AI engine (1–3 GB). Every future launch opens instantly with no setup.

> **Python 3.10+ is required** for the setup wizard.  
> Install from [python.org](https://www.python.org/downloads/) and tick **"Add Python to PATH"**.  
> After setup, Python runs entirely in the background — you never need to touch it again.

### Step 4 — Transcribe

1. Click **Transcribe** and select your audio or video file
2. Go to **Quality** to choose model size and device
3. Go to **Save** to choose your export formats
4. Click **Transcribe**

---

### CPU vs GPU

| | CPU | GPU |
|---|---|---|
| Setup download | ~1 GB | ~2–3 GB |
| Transcription speed | ~0.3–0.5× realtime | ~8–15× realtime |
| Hardware required | Any Windows PC | NVIDIA GPU + driver 525+ |

The wizard detects your GPU automatically. You can override the device in the **Quality** panel.

---

### Models

| Model | Download size | Best for |
|---|---|---|
| `tiny` | ~75 MB | Quick preview, low accuracy |
| `base` | ~145 MB | Fast drafts |
| `small` | ~465 MB | Good balance of speed and accuracy |
| `medium` | ~1.5 GB | High accuracy |
| `large-v2` *(default)* | ~3 GB | Best quality, recommended |
| `large-v3` | ~3 GB | Latest version of large |

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

---

### Troubleshooting

**"Python not found"** — Install [Python 3.10+](https://www.python.org/downloads/) and tick "Add Python to PATH". Then re-run the app.

**Setup fails mid-download** — Click **Retry**. The wizard resumes and skips already-installed packages.

**CUDA out of memory** — Lower Batch Size in the Quality panel. Try 8, then 4.

**Alignment fails** — Disable word timestamps in the Save panel. SRT, VTT, and TXT still export without them.

**Transcription is slow on CPU** — Use a smaller model (`small` or `base`).

**Anything else** — Open a [GitHub issue](../../issues) and paste the Activity log output.

---

---

# For Developers

> Clone, run one script, and you're in.

### Requirements

- Python 3.10, 3.11, 3.12, or 3.13
- Git
- Windows (macOS support planned — see roadmap)
- NVIDIA GPU recommended but not required

### Quick start

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat
```

`run.bat` creates a `.venv`, installs the correct PyTorch build for your GPU, installs WhisperX and all UI dependencies, and launches the app. Every subsequent run opens instantly.

### Project structure

```
whisperx-transcriber/
│
├── app.py                  Main GUI application
├── launcher.py             Thin entry point used by the packaged .exe
├── setup_wizard.py         First-run wizard (frozen inside the .exe)
├── transcribe.py           Headless CLI for scripting and batch use
│
├── core/
│   └── pipeline.py         All WhisperX pipeline logic — no GUI dependencies
│
├── run.bat                 Windows developer launcher
│
├── packaging/
│   ├── build.bat           Builds the thin launcher exe + portable zip
│   └── launcher.spec       PyInstaller spec — GUI only, no ML packages
│
├── tests/
│   └── test_pipeline.py    Unit + WER tests for core pipeline
│
└── assets/
    ├── icon.ico
    ├── screenshots/        README screenshots
    └── samples/            Sample audio files
```

### Architecture — thin launcher pattern

```
WhisperXTranscriber.exe  (PyInstaller onedir, ~19 MB)
  └── Python runtime + customtkinter + Pillow  (GUI only)
  └── setup_wizard (frozen inside)
      └── On first run: pip-installs whisperx + torch into runtime/
          └── On all later runs: spawns runtime/python app.py
```

This keeps the distributable tiny and means AI engine updates don't require re-downloading the whole app.

### Building the release zip

```bash
packaging\build.bat   # requires .venv (run run.bat once first)
# Output: dist/release/WhisperXTranscriber.zip
```

### CLI usage

```bash
python transcribe.py audio.mp3
python transcribe.py audio.mp3 --language ur --model large-v2
python transcribe.py audio.mp3 --device cpu --output srt vtt
python transcribe.py audio.mp3 --model-dir D:\models
```

---

---

## Roadmap

This project is built and maintained by a single developer — a working student engineer and part-time researcher. Development happens in spare time, but the vision is clear. Here's where it's going:

### Coming next

- **Cancel button** — stop a transcription mid-run without closing the app
- **Real progress tracking** — percentage-based progress instead of indeterminate animation
- **macOS `.app` bundle** — portable build for Mac, same thin-launcher pattern

### Planned features

- **Drag-and-drop** file input directly onto the window
- **Batch folder transcription** — drop a folder, transcribe everything as a queue
- **Speaker diarization** — identify who said what, with per-speaker labels in the output
- **Translation mode** — transcribe and translate to English in one pass
- **Custom vocabulary** — prime the model with domain-specific terms for better accuracy
- **Auto-update check** — get notified when a new version is available

### Longer term

- **Linux AppImage** — after macOS is stable
- **Local crash logs** — rotating log file so errors are never silently lost

> If any of these matter to you, the fastest way to make them happen is to [support the project](#support-the-project) or open an issue describing your use case.

---

## Support the Project

This app is completely free and always will be. But building and maintaining it takes real time — time that competes with coursework, research, and everything else that comes with being a student.

If WhisperX Transcriber has been useful to you, consider supporting it:

| | |
|---|---|
| **♥ GitHub Sponsors** | [![Sponsor](https://img.shields.io/badge/Sponsor-GitHub-ea4aaa?style=flat&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/ibrahimqureshae) Monthly or one-time, directly through GitHub |
| **PayPal** | [![Donate](https://img.shields.io/badge/Donate-PayPal-0070ba?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/mibrahimqr) One-time donation, any amount |
| **★ Star the repo** | [![Stars](https://img.shields.io/github/stars/ibrahimqureshae/whisperx-transcriber?style=flat&logo=github)](https://github.com/ibrahimqureshae/whisperx-transcriber/stargazers) Free, takes two seconds, helps discoverability |
| **Share it** | Tell a colleague, post in a community, recommend it to someone who needs it |

Every contribution — financial or otherwise — directly enables more development time and faster feature delivery.

---

## Free and open source

WhisperX Transcriber exists because powerful AI tools should be accessible to everyone — not locked behind expensive subscriptions or a command line that most people will never open.

Built entirely on open-source foundations: OpenAI's Whisper, WhisperX, faster-whisper, and customtkinter. Released under the MIT license — free to use, modify, fork, and build on, forever.

No telemetry. No tracking. No hidden network calls. Every line of code that runs on your machine is readable in this repo.

---

## Contributing

Contributions are genuinely welcome — bug reports, feature requests, UI improvements, language support, or just testing on different hardware.

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat
```

The codebase is intentionally small and readable. `app.py` is the entire GUI, `core/pipeline.py` is all the AI logic. A new contributor can understand the whole project in an afternoon.

Open an [issue](../../issues) or a pull request — both are welcome.

---

## Tech stack

| Layer | Library |
|---|---|
| GUI | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Transcription | [WhisperX](https://github.com/m-bain/whisperX) |
| ASR backend | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) |
| Inference runtime | [CTranslate2](https://github.com/OpenNMT/CTranslate2) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

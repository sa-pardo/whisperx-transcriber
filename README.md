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

## Quick Access

**Is this for me?**
[Why use this?](#why-use-this) · [What you can do with it](#what-you-can-do-with-it) · [Supported languages](#supported-languages) · [Who is this for?](#who-is-this-for) · [See it in action](#see-it-in-action)

**Get Started**
[Download & install](#get-started) · [First-time setup](#3-complete-the-one-time-setup) · [CPU vs GPU](#cpu-vs-gpu) · [How to transcribe](#4-start-transcribing)

**Using the App**
[What the app looks like](#what-the-app-looks-like) · [Choosing a model](#choosing-a-model) · [Output formats](#output-formats) · [Troubleshooting](#troubleshooting)

**Build & Hack**
[Quick start](#quick-start) · [Project structure](#project-structure) · [How it works](#how-it-works-under-the-hood) · [CLI usage](#command-line-usage) · [Package a release](#package-a-release)

**Community & Support**
[What's coming](#whats-coming) · [Support the project](#support-the-project) · [Help build it](#help-build-it) · [What it's built on](#what-its-built-on) · [License](#license)

---

## Why use this?

Most transcription tools are either expensive cloud services that upload your audio to a remote server, or complex Python scripts that require technical setup. WhisperX Transcriber is neither.

- **Your audio never leaves your machine.** Everything runs locally — no cloud, no API key, no subscription.
- **One-time setup, then works forever offline.** The AI engine downloads once (~1–3 GB). After that, no internet needed — ever.
- **No terminal, no Python knowledge required.** Extract the zip, run the exe, click through a one-time setup wizard. Done.
- **Fast.** On a modern NVIDIA GPU, it transcribes faster than realtime. On CPU it's still practical for short and medium recordings.
- **Accurate.** Powered by OpenAI's Whisper large-v2 — one of the best open-source speech recognition models available.
- **Word-level timestamps.** Every word is timed precisely, not just sentence segments — essential for subtitles, content search, and editing.
- **Fully open source.** No telemetry, no tracking, no surprises. Every line of code is readable in this repo.

---

## What the app looks like

Four clean panels — everything is a click away, nothing is buried.

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

## What you can do with it

- Transcribes **audio and video files** to text with word-level timestamps
- Exports to **SRT, VTT, TXT, TSV, JSON**, or a custom **Word JSON** format
- Supports **20 languages** in the GUI, **99 languages** via the CLI
- Auto-detects your **NVIDIA GPU** and uses CUDA — falls back to CPU automatically
- Strips silence with a built-in **Voice Activity Detection (VAD)** filter
- Produces **karaoke-style subtitles** with word-by-word highlighting in SRT/VTT
- Runs **100% offline** after the one-time first-run setup

---

## See it in action

### English — "The quick brown fox…"

🔊 [**Download sample audio**](assets/samples/English_test.wav) *(WAV, ~10 seconds)*

Transcribed with `large-v2`, word timestamps enabled:

**Plain text**
```
The quick brown fox jumps over the lazy dog.
```

**SRT — word-level, every word precisely timed**
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

**Word JSON — per-word confidence scores**
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

Language auto-detected as `ur`. Right-to-left scripts work natively — no special setup needed.

**Plain text**
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

> Urdu, Arabic, Persian, and Pashto all work out of the box. The model reads right-to-left text naturally — no post-processing or font tweaks required.

---

## Download once, use forever

The app is built around one principle: **pay the download cost once, use it forever**.

```
First launch  (internet required — one time only)
  └── Setup Wizard installs the AI engine: torch + whisperX  (~1–3 GB)
      └── Saved to the runtime/ folder next to the app
          └── Every launch after this: fully offline, opens instantly
```

AI models (e.g. large-v2) are also cached on first use and never re-downloaded. Transcription works with no internet connection at all after that — even on a plane.

---

## Supported languages

**20 languages** are available in the dropdown, with **Auto-detect** as the default:

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

The underlying Whisper model supports **99 languages** in total — all accessible via the CLI using any ISO 639-1 code.

---

## Who is this for?

- **Journalists and researchers** — transcribe interviews and lectures with accurate timestamps
- **Content creators** — generate subtitles for videos in minutes instead of hours
- **Translators** — get a clean, timestamped base transcript before you start
- **Students** — transcribe lectures, seminars, and recorded classes offline
- **Anyone working with Arabic, Urdu, Persian, Pashto, or other RTL languages** — full native support
- **Privacy-conscious users** — nothing is uploaded anywhere, ever

---

---

# Get Started

> No terminal, no Python knowledge required. Just download, extract, and run.

### 1. Download the app

Head to the [**Releases**](../../releases) tab and grab the latest `WhisperXTranscriber.zip` — it's about 19 MB.

### 2. Extract and launch

- Unzip anywhere you like — `C:\Apps\WhisperXTranscriber\` works great
- Double-click `WhisperXTranscriber.exe`
- **No installer, no admin rights needed** — it's fully portable

### 3. Complete the one-time setup

<table>
  <tr>
    <td align="center">
      <img src="assets/screenshots/First_Time_Setup.png" width="360" alt="Setup wizard welcome screen"/><br/>
      <sub>Your GPU is detected automatically — the right CUDA build is selected for you</sub>
    </td>
    <td align="center">
      <img src="assets/screenshots/Setup_Ongoing.png" width="360" alt="Setup wizard installing"/><br/>
      <sub>torch + WhisperX are downloading — this only ever happens once</sub>
    </td>
  </tr>
</table>

On first launch, the **Setup Wizard** opens and handles everything — including Python if it's not already on your machine. If Python isn't found, the wizard starts downloading and installing Python 3.13 automatically after a brief pause. No clicks, no manual steps needed.

Once Python is ready, the wizard downloads the AI engine (1–3 GB). This is a one-time step. Every launch after this opens instantly.

> Prefer to install Python yourself? Get it from [python.org/downloads](https://www.python.org/downloads/) and tick **"Add Python to PATH"** on the first screen.

### 4. Start transcribing

1. Click **Transcribe** in the sidebar and select your audio or video file
2. Go to **Quality** to pick your model and device
3. Go to **Save** to choose which formats you want to export
4. Hit **Transcribe** — the Activity panel shows you what's happening in real time

---

### CPU vs GPU

| | CPU | GPU (NVIDIA) |
|---|---|---|
| Setup download | ~1 GB | ~2–3 GB |
| Transcription speed | ~0.3–0.5× realtime | ~8–15× realtime |
| Hardware needed | Any Windows PC | NVIDIA GPU + driver 525+ |

The wizard detects your GPU automatically. You can override the device any time in the **Quality** panel.

---

### Choosing a model

Models download on first use and are cached — you never re-download them.

| Model | Size | Best for |
|---|---|---|
| `tiny` | ~75 MB | Quick test, low accuracy |
| `base` | ~145 MB | Fast rough drafts |
| `small` | ~465 MB | Good balance of speed and quality |
| `medium` | ~1.5 GB | High accuracy |
| `large-v2` *(default)* | ~3 GB | Best quality — start here |
| `large-v3` | ~3 GB | Newest large model |

Not sure which to pick? Start with `large-v2`. Drop down to `small` if you need speed or have limited disk space.

---

### Output formats

| Format | What you get |
|---|---|
| `SRT` | Standard subtitles — drag into VLC, YouTube, Premiere, DaVinci Resolve |
| `VTT` | WebVTT subtitles — for web video players and browsers |
| `TXT` | Clean plain text — no timestamps, just the words |
| `TSV` | Tab-separated — start/end times per segment, easy to open in Excel |
| `JSON` | Full segment-level data with all metadata |
| `Word JSON` | Per-word `{word, start, end, score}` — for developers and pipelines |

You can select multiple formats at once — all files save to the same folder.

---

### Troubleshooting

**"Python not found" / orange warning in the setup wizard**  
The wizard starts installing Python 3.13 automatically — just wait a moment. If you'd rather install it yourself, go to [python.org/downloads](https://www.python.org/downloads/) and tick **"Add Python to PATH"** on the first screen, then click "Check again" in the wizard.

**Setup stops or fails mid-download**  
Click **Retry** — the wizard picks up where it left off and skips packages that are already installed.

**"CUDA out of memory" during transcription**  
Go to **Quality** and lower the Speed (batch size) value. Try 8, then 4.

**Word alignment failed**  
Turn off **Word timestamps** in the Save panel. SRT, VTT, and TXT still export without word-level timing.

**Transcription is very slow**  
Switch to a smaller model (`small` or `base`) in the Quality panel.

**Something else is wrong**  
Open a [GitHub issue](../../issues) and paste the output from the **Activity** panel — that's the fastest way to get help.

---

---

# Build & Hack

> Clone the repo, run one command, and you're developing.

### What you need

- Python 3.10, 3.11, 3.12, or 3.13
- Git
- Windows *(macOS support is on the roadmap)*
- An NVIDIA GPU is helpful but not required

### Quick start

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat
```

`run.bat` handles everything on first run: creates a `.venv`, detects your GPU, installs the right PyTorch build, installs WhisperX and the UI dependencies, then launches the app. Every run after the first opens instantly.

### Project structure

```
whisperx-transcriber/
│
├── app.py                  Main GUI — the entire interface (~1000 lines)
├── launcher.py             Thin .exe entry point — checks setup, spawns app
├── setup_wizard.py         First-run wizard, frozen inside the .exe
├── transcribe.py           Headless CLI for scripting and batch work
│
├── core/
│   └── pipeline.py         All AI/WhisperX logic — zero GUI dependencies
│
├── run.bat                 Developer launcher for Windows
│
├── packaging/
│   ├── build.bat           Builds the .exe and packages the portable zip
│   └── launcher.spec       PyInstaller spec — GUI only, no ML packages
│
├── tests/
│   └── test_pipeline.py    Unit + WER tests for the core pipeline
│
└── assets/
    ├── icon.ico
    ├── screenshots/        README screenshots
    └── samples/            Sample audio files
```

### How it works under the hood

The distributed `.exe` is intentionally tiny (~19 MB) — it contains **no AI packages whatsoever**:

```
WhisperXTranscriber.exe  (PyInstaller onedir)
  └── Python runtime + customtkinter + Pillow  (GUI shell only)
  └── setup_wizard  (frozen inside the exe)
      └── First run  →  pip-installs torch + whisperx into runtime/
          └── All later runs  →  spawns runtime/python.exe app.py
```

This means the distributable stays small and AI engine updates don't require users to re-download the whole app.

### Package a release

```bash
# Requires .venv — run run.bat once first
packaging\build.bat

# Output
dist/release/WhisperXTranscriber.zip
```

### Command-line usage

For scripting, batch processing, or accessing all 99 supported languages:

```bash
# Basic usage
python transcribe.py audio.mp3

# With options
python transcribe.py audio.mp3 --language ur --model large-v2
python transcribe.py audio.mp3 --device cpu --output srt vtt txt
python transcribe.py audio.mp3 --model-dir D:\models
```

| Option | Values | Default |
|---|---|---|
| `--model` | `tiny` `base` `small` `medium` `large-v2` `large-v3` | `large-v2` |
| `--language` | Any ISO 639-1 code (`en`, `ar`, `ur`, `fa` …) | auto-detect |
| `--device` | `cuda` `cpu` | auto-detect |
| `--output` | `srt` `vtt` `txt` `tsv` `json` `word_json` | `word_json` |
| `--model-dir` | Path to model cache folder | `./Models` |

---

---

## What's Coming

This project is built and maintained by a single developer — a working student engineer doing part-time research. Development happens in spare time, but the vision is clear and the roadmap is real.

### Up next

- **Cancel button** — stop a transcription mid-run without closing the app
- **Real progress tracking** — show percentage complete instead of an indeterminate bar
- **macOS `.app` bundle** — a proper portable build for Mac, same thin-launcher pattern

### On the roadmap

- **Drag-and-drop** — drop audio or video files directly onto the window
- **Batch transcription** — drop a folder, process everything as a queue
- **Speaker diarization** — who said what, with per-speaker labels in the output
- **Translation mode** — transcribe and translate to English in one pass
- **Custom vocabulary** — give the model domain-specific terms for better accuracy
- **Auto-update notifications** — know when a new version is available

### The bigger picture

- **Linux AppImage** — after macOS is solid
- **Local error logs** — rotating crash log so nothing fails silently again

> Have a feature you really want? The fastest way to make it happen is to [support the project](#support-the-project) or open an issue describing your use case.

---

## Support the Project

I'm a working student engineer doing part-time research, building this entirely in my spare time. WhisperX Transcriber is free and always will be — but if it's saved you hours of manual transcription work, consider buying me a coffee to keep development going.

<p align="center">
  <a href="https://github.com/sponsors/ibrahimqureshae">
    <img src="https://img.shields.io/badge/Sponsor%20on%20GitHub-%E2%99%A5-ea4aaa?style=for-the-badge&logo=githubsponsors&logoColor=white" alt="Sponsor on GitHub"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://www.paypal.me/mibrahimqr">
    <img src="https://img.shields.io/badge/Donate%20via%20PayPal-0070ba?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate via PayPal"/>
  </a>
</p>

### Pick your level

| Tier | Amount | What it means |
|---|---|---|
| ☕ **A coffee** | $3 / month | Keeps me caffeinated through late-night coding sessions |
| 🍕 **A slice** | $10 / month | Covers tools, storage, and GPU time for testing |
| 📚 **A textbook** | $25 / month | Offsets research and coursework costs so I can spend more time building |
| 🚀 **A booster** | $50 / month | Priority feature requests — you tell me what to build next |

> **Prefer a one-time contribution?** Any amount via [PayPal](https://www.paypal.me/mibrahimqr) is just as appreciated — there's no minimum. Even $1 is a genuine signal that this work matters.

### Not ready to donate? No worries.

There are other ways to help that cost nothing:

- **★ Star the repo** — takes two seconds, makes the project easier to find
- **Share it** — tell a colleague, post in a community, or recommend it to someone who'd find it useful
- **Report a bug or request a feature** — a good issue is a real contribution

Every bit of support — financial or otherwise — directly translates to more time building features and fixing bugs.

---

## Open source, no strings attached

WhisperX Transcriber exists because powerful AI tools should be accessible to everyone — not locked behind expensive subscriptions or a command line most people will never open.

Built entirely on open-source foundations: OpenAI's Whisper, WhisperX, faster-whisper, and customtkinter. Released under the MIT license — free to use, modify, fork, and build on, forever.

No telemetry. No tracking. No hidden network calls. Every line of code that runs on your machine is here in this repo.

---

## Help build it

Contributions are genuinely welcome — bug reports, feature requests, UI improvements, new language support, or just testing on different hardware and sharing what you find.

```bash
git clone https://github.com/ibrahimqureshae/whisperx-transcriber.git
cd whisperx-transcriber
run.bat
```

The codebase is intentionally small. `app.py` is the entire GUI, `core/pipeline.py` is all the AI logic — a new contributor can understand the whole project in an afternoon.

Open an [issue](../../issues) to report a bug or suggest a feature. Open a pull request if you've already built something — both are welcome.

---

## What it's built on

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

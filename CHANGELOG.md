# Changelog

All notable changes to WhisperX Transcriber are documented here.

## [Unreleased]

## [v1.3.4] — 2026-10-18

### Fixed
- Allow Windows portable setup and repair to complete when TorchCodec is installed
  at the required version but its optional native FFmpeg libraries cannot load.
- Keep strict dependency checks for PyTorch, WhisperX, pyannote and other required
  modules; report a concise, non-blocking warning for TorchCodec decoding.
- Avoid repeating pyannote's verbose TorchCodec DLL traceback during setup while
  keeping other warnings visible.

### Changed
- Add Windows regression tests for broken TorchCodec native imports, required
  dependency failures and successful setup completion.

## [v1.3.3] — 2026-10-18

### Fixed
- Prevent the first-run wizard from reopening after a slow cold start or idle
  period. The launcher now checks installed package metadata without importing
  PyTorch native libraries on every launch.
- Distinguish missing dependencies from inconclusive startup checks. Timeouts
  and unexpected probe errors are logged, and the launcher attempts normal
  startup instead of reinstalling the backend.
- Log early GUI startup failures and offer an explicit repair path through
  `WhisperXTranscriber.exe --repair`.
- Make repair recreate and verify the managed `runtime/` environment,
  including CPU/GPU and core dependency imports, while keeping downloaded
  models and user settings.

### Changed
- Extend Windows regression tests for dependency checks, error reporting,
  and the repair workflow.

## [v1.3.2] — 2026-10-13

### Fixed
- Prevent the PyInstaller launcher from passing its bundled Tcl/Tk library paths
  to the external Python runtime. This resolves silent startup failures when
  the bundled Tcl/Tk version differs from the runtime's version.

## [v1.3.1] — 2026-10-13

### Fixed
- Detect NVIDIA CUDA support from both `CUDA Version` and `CUDA UMD Version`
  in `nvidia-smi`, so newer compatible drivers select GPU PyTorch wheels.

## [v1.3.0] — 2026-10-04

### Added
- Optional speaker diarization in the GUI and CLI, with minimum/maximum speaker
  bounds and word/segment speaker labels through WhisperX Community-1.
- HF token remembered in project-local `settings.json`, masked entry, automatic
  saving, deletion, environment fallback, and redacted diagnostics.
- CLI batch size, precision, output folder, `all` output formats and flag aliases.

### Changed
- Pin compatible inference packages, install portable FFmpeg, and repair CPU-only
  PyTorch environments on NVIDIA hardware using CUDA 12.8 wheels.
- Align diarized jobs when word timestamps are enabled, release GPU memory between
  stages, and stop before exporting when requested diarization fails.
- Version portable runtime setup and exclude credential files from release ZIPs.
- Windows `run.bat` reuses local `.venv` Python and local or PATH-installed uv,
  downloading uv and Python inside the project when missing. Package installation
  uses uv and resumes when an existing virtual environment lacks dependencies.

## [v1.2.0] — 2026-06-09

### Added
- **Instant Cancel** — transcription now runs in a separate process that is
  terminated immediately when you click Cancel, instead of waiting for the
  current stage to finish.

### Changed
- **Redesigned interface** — consolidated into a single, fixed-size Transcribe
  screen: file, language, model, device, output formats, save location, and
  options are all in one place. Advanced settings moved behind a dedicated tab.
- Cleaner dropdowns, improved text contrast and readability throughout.
- Activity log now appears only while a job is running and auto-hides when done.

## [v1.1.4] — 2026-06-09

### Changed
- Removed progress bar and cancel button mentions from docs (not yet implemented)

## [v1.1.3] — 2026-06-07

### Added
- Bundled FFmpeg via imageio-ffmpeg — no separate download needed
- Real-time download progress during setup wizard

### Fixed
- FFmpeg resolution now works reliably across all configurations

## [v1.1.0] — 2026-06-07

### Added
- Full GUI desktop app for Windows (customtkinter)
- One-time Setup Wizard with automatic GPU/CPU detection
- Support for 20 languages in the GUI dropdown, 99 via CLI
- Word-level timestamp alignment via WhisperX
- Export to SRT, VTT, TXT, TSV, JSON, and Word JSON formats
- CPU and GPU (CUDA) transcription support
- Fully offline operation after one-time setup
- VAD (Voice Activity Detection) silence stripping
- Karaoke-style word-highlighted subtitle export
- Model support: tiny, base, small, medium, large-v2, large-v3
- Headless CLI (transcribe.py) for scripting and batch use
- Portable distribution — no installer, no admin rights required
- Thin launcher pattern — ~19 MB exe, AI engine installed separately
- Auto-detection of NVIDIA GPU with CPU fallback

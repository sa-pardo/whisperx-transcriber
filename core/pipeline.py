"""
WhisperX pipeline — pure computation, no GUI dependencies.
Shared by app.py (_worker) and transcribe.py (main).
"""
import os
import json
import gc


STANDARD_FORMATS = ("srt", "vtt", "txt", "tsv", "json")
DIARIZATION_MODEL = "pyannote/speaker-diarization-community-1"
_cuda_dll_directory = None


def validate_diarization_options(enabled, min_speakers=None,
                                 max_speakers=None, hf_token=None) -> tuple:
    """Normalize optional speaker bounds; fail before loading any models."""
    if not enabled:
        return None, None

    def speaker_count(value, label):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError(f"{label} must be a positive integer or empty.")
        try:
            count = int(value)
        except ValueError:
            raise ValueError(f"{label} must be a positive integer or empty.") from None
        if count < 1:
            raise ValueError(f"{label} must be a positive integer or empty.")
        return count

    minimum = speaker_count(min_speakers, "Min speakers")
    maximum = speaker_count(max_speakers, "Max speakers")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Min speakers cannot exceed Max speakers.")
    if not isinstance(hf_token, str) or not hf_token.strip():
        raise ValueError("Speaker diarization requires an HF Token. Enter it in Settings "
                         "or set HF_TOKEN.")
    return minimum, maximum


def cleanup_memory() -> None:
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def format_srt_timestamp(seconds: float) -> str:
    """Convert a float number of seconds to SRT timestamp format: HH:MM:SS,mmm"""
    assert seconds >= 0, f"Timestamp must be non-negative, got {seconds}"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = round((seconds % 1) * 1000)
    # Handle rounding up to a full second
    if ms == 1000:
        ms = 0
        secs += 1
        if secs == 60:
            secs = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def detect_device(requested: str) -> tuple:
    """
    Returns (device, t_dev, a_dev).
      device — resolved device: "cuda", "mps", or "cpu"
      t_dev  — transcription device (MPS uses CPU; whisperx doesn't support MPS for ASR)
      a_dev  — alignment device (MPS is fine for alignment)
    """
    import torch
    if requested == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    else:
        device = requested
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable. Run setup to install CUDA PyTorch, "
                           "check the NVIDIA driver, or select CPU.")
    if device == "cuda" and os.name == "nt":
        # CTranslate2 also needs to locate the CUDA/cuDNN DLLs shipped by torch.
        global _cuda_dll_directory
        lib_dir = os.path.join(os.path.dirname(torch.__file__), "lib")
        if _cuda_dll_directory is None and os.path.isdir(lib_dir):
            _cuda_dll_directory = os.add_dll_directory(lib_dir)
            os.environ["PATH"] = lib_dir + os.pathsep + os.environ.get("PATH", "")
    t_dev = "cpu" if device == "mps" else device
    a_dev = device
    return device, t_dev, a_dev


def resolve_compute(t_dev: str, compute: str) -> tuple:
    """
    Returns (compute_type, was_adjusted).
    float16 and int8_float16 are not supported on CPU — falls back to int8.
    """
    if t_dev == "cpu" and compute in ("float16", "int8_float16"):
        return "int8", True
    return compute, False


def _dir_size(path: str) -> int:
    """Total size in bytes of every file under path (0 if it doesn't exist)."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def download_model(model: str, model_dir: str,
                   progress_cb=None, cancel_cb=None) -> None:
    """
    Pre-download a faster-whisper model with real progress reporting.

    progress_cb(done_bytes, total_bytes) is called ~3x/sec while downloading,
    for display only (exceptions from it are ignored).  cancel_cb() is polled
    between files; return True from it to abort the download.

    Stores into {model_dir}/hub so a later load_model() finds it cached and
    does not re-download.  Raises on download failure — the caller may fall
    back to load_model(), which downloads the model itself (no progress).

    Progress is measured by polling the size of the download folder on disk
    rather than via tqdm: huggingface_hub only routes a custom tqdm to its
    outer "Fetching N files" counter, not the per-byte file bars, so a tqdm
    hook reports file-count progress (effectively 0%) instead of bytes.
    """
    import threading
    import time as _time
    from huggingface_hub import snapshot_download

    repo       = f"Systran/faster-whisper-{model}"
    cache_dir  = os.path.join(model_dir, "hub")
    model_root = os.path.join(cache_dir, f"models--Systran--faster-whisper-{model}")

    # Total download size, fetched up front so the fraction has a fixed
    # denominator (the progress bar fills smoothly from 0 to 100%).
    total_size = 0
    try:
        from huggingface_hub import HfApi
        info = HfApi().model_info(repo, files_metadata=True)
        total_size = sum((s.size or 0) for s in (info.siblings or []))
    except Exception:
        total_size = 0

    stop = threading.Event()

    def _poll():
        while not stop.is_set():
            sz = _dir_size(model_root)
            try:
                progress_cb(min(sz, total_size), total_size)
            except Exception:
                pass
            stop.wait(0.3)

    poller = None
    if progress_cb is not None and total_size:
        poller = threading.Thread(target=_poll, daemon=True)
        poller.start()

    # A tqdm subclass purely to honor cancellation (checked between files).
    cancel_tqdm = None
    if cancel_cb is not None:
        try:
            from huggingface_hub.utils import tqdm as _BaseTqdm
        except Exception:
            from tqdm.auto import tqdm as _BaseTqdm

        class _CancelTqdm(_BaseTqdm):
            def update(self, n=1):
                if cancel_cb():
                    raise RuntimeError("cancelled")
                return super().update(n)

        cancel_tqdm = _CancelTqdm

    try:
        kwargs = {"cache_dir": cache_dir, "max_workers": 1}
        if cancel_tqdm is not None:
            try:
                snapshot_download(repo, tqdm_class=cancel_tqdm, **kwargs)
            except TypeError:
                snapshot_download(repo, **kwargs)
        else:
            snapshot_download(repo, **kwargs)
    finally:
        stop.set()
        # Land cleanly on 100% (unless we were cancelled)
        if progress_cb is not None and total_size and not (cancel_cb and cancel_cb()):
            try:
                progress_cb(total_size, total_size)
            except Exception:
                pass


def load_model(model: str, t_dev: str, compute: str, language, beam: int):
    """Load and return a WhisperX ASR model."""
    import whisperx
    return whisperx.load_model(
        model, t_dev,
        compute_type=compute,
        language=language,
        asr_options={"beam_size": beam},
    )


def _ensure_ffmpeg_on_path() -> None:
    """
    whisperx.load_audio() invokes a bare ``ffmpeg``.  imageio-ffmpeg ships a
    version-named binary (e.g. ``ffmpeg-win-x86_64-v7.1.exe``), which a bare
    ``ffmpeg`` call cannot find — that is the cause of ``[WinError 2]``.

    Expose the bundled binary under the plain name ``ffmpeg(.exe)`` and put its
    folder on PATH so the call resolves.  Idempotent and best-effort.
    """
    import shutil
    if shutil.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return
    if not exe or not os.path.isfile(exe):
        return

    bin_dir = os.path.dirname(exe)
    name    = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    target  = os.path.join(bin_dir, name)
    if not os.path.isfile(target):
        try:
            os.link(exe, target)        # instant, no extra disk space (same volume)
        except Exception:
            try:
                shutil.copy2(exe, target)   # fallback if hardlink unsupported
            except Exception:
                return
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


def load_audio(path: str):
    """Load audio from file and return audio array."""
    import whisperx
    _ensure_ffmpeg_on_path()
    return whisperx.load_audio(path)


def transcribe(model, audio, batch_size: int, language) -> tuple:
    """
    Transcribe audio. Returns (result, detected_language).
    Pass language=None to auto-detect.
    """
    kwargs = {"batch_size": batch_size}
    if language:
        kwargs["language"] = language
    result = model.transcribe(audio, **kwargs)
    detected = result.get("language", language or "en")
    return result, detected


def align(result: dict, detected_lang: str, a_dev: str, audio) -> dict:
    """
    Word-level alignment. Returns updated result with word timestamps.
    Tries a_dev first; falls back to CPU if that fails.
    Preserves the "language" key that whisperx.align() drops.
    Raises if alignment fails on both devices.
    """
    import whisperx

    def _do_align(device):
        model_a, meta = whisperx.load_align_model(
            language_code=detected_lang, device=device)
        return whisperx.align(result["segments"], model_a, meta, audio, device)

    try:
        aligned = _do_align(a_dev)
    except Exception:
        if a_dev == "cpu":
            raise
        aligned = _do_align("cpu")

    aligned.setdefault("language", detected_lang)
    return aligned


def diarize(result: dict, audio, device: str, hf_token: str,
            min_speakers: int | None = None, max_speakers: int | None = None,
            model_dir: str | None = None, progress_cb=None) -> dict:
    """Assign speaker labels using the already-decoded 16 kHz audio array."""
    minimum, maximum = validate_diarization_options(
        True, min_speakers, max_speakers, hf_token)
    from whisperx.diarize import DiarizationPipeline, assign_word_speakers

    model = None
    try:
        try:
            model = DiarizationPipeline(
                model_name=DIARIZATION_MODEL, token=hf_token.strip(),
                device=device,
                cache_dir=os.path.join(model_dir, "hub") if model_dir else None)
        except Exception as exc:
            response = getattr(exc, "response", None)
            denied = getattr(response, "status_code", None) in (401, 403)
            missing_pipeline = isinstance(exc, AttributeError) and "NoneType" in str(exc)
            if denied or missing_pipeline or type(exc).__name__ == "GatedRepoError":
                raise RuntimeError(
                    "Could not access the diarization model. Check your HF Token's "
                    "read permissions and accept the conditions at "
                    f"https://huggingface.co/{DIARIZATION_MODEL}.") from exc
            raise RuntimeError(f"Could not load the diarization model: {exc}") from exc
        segments = model(audio, min_speakers=minimum, max_speakers=maximum,
                         progress_callback=progress_cb)
        return assign_word_speakers(segments, result)
    except Exception as exc:
        if "out of memory" in str(exc).lower():
            raise RuntimeError("Diarization ran out of GPU memory. Close other GPU "
                               "applications or select CPU.") from exc
        raise
    finally:
        del model
        cleanup_memory()


def export(result: dict, formats: list, out_dir: str,
           audio_path: str, opts: dict) -> list:
    """
    Export result to the requested formats.
    Returns list of (fmt, path, error) tuples — error is None on success.
    opts keys: max_width, max_count, highlight.
    """
    from whisperx.utils import get_writer

    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    results = []

    if "word_json" in formats:
        words = [w for seg in result["segments"] for w in seg.get("words", [])]
        path = os.path.join(out_dir, base + "_words.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(words, fh, indent=2, ensure_ascii=False)
            results.append(("word_json", path, None))
        except Exception as e:
            results.append(("word_json", None, str(e)))

    writer_opts = {
        "max_line_width":  opts.get("max_width"),
        "max_line_count":  opts.get("max_count"),
        "highlight_words": opts.get("highlight", False),
    }
    for fmt in formats:
        if fmt == "word_json":
            continue
        path = os.path.join(out_dir, base + "." + fmt)
        try:
            get_writer(fmt, out_dir)(result, audio_path, writer_opts)
            results.append((fmt, path, None))
        except Exception as e:
            results.append((fmt, None, str(e)))

    return results

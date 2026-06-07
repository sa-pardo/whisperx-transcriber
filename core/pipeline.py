"""
WhisperX pipeline — pure computation, no GUI dependencies.
Shared by app.py (_worker) and transcribe.py (main).
"""
import os
import json


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


def load_model(model: str, t_dev: str, compute: str, language, beam: int):
    """Load and return a WhisperX ASR model."""
    import whisperx
    return whisperx.load_model(
        model, t_dev,
        compute_type=compute,
        language=language,
        asr_options={"beam_size": beam},
    )


def load_audio(path: str):
    """Load audio from file and return audio array."""
    import whisperx
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

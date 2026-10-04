"""
WhisperX Transcriber — headless CLI

Usage:
    python transcribe.py <audio_or_video_file> [options]

Options:
    --model      Model name (default: large-v2)
                 Choices: tiny, base, small, medium, large-v2, large-v3
    --language   Language code (default: auto-detect)
                 Examples: en, ar, fr, de, es, zh, ja, ur, fa
    --device     cuda | cpu (default: auto-detect)
    --output     Output format: word_json, srt, vtt, txt, tsv, json (default: word_json)
    --model-dir  Where to cache downloaded models (default: ./Models)
    --diarize    Assign speaker labels (requires HF token and model access)
    --min_speakers / --max_speakers  Optional positive speaker bounds
    --hf_token   HF token; remembered in project-local settings.json
    --batch_size / --compute_type   Inference settings
    --output_dir / --output_format  Output folder and format (including all)

Examples:
    python transcribe.py audio.mp3
    python transcribe.py audio.mp3 --language ar --model large-v2
    python transcribe.py audio.mp3 --device cpu --output srt
    python transcribe.py audio.mp3 --model-dir D:\\models
"""
import os
import sys
import argparse
from core import pipeline, settings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="WhisperX headless transcription CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audio", help="Path to audio or video file")
    parser.add_argument("--model",     default="large-v2",
                        help="Whisper model (default: large-v2)")
    parser.add_argument("--language",  default=None,
                        help="Language code, e.g. en, ar, fr (default: auto-detect)")
    parser.add_argument("--device",    default="auto",
                        help="cuda | cpu | auto (default: auto)")
    parser.add_argument("--output", "--output_format", "--output-format",
                        dest="output", default="word_json",
                        choices=["all", "word_json", *pipeline.STANDARD_FORMATS],
                        help="Output format (default: word_json)")
    parser.add_argument("--model-dir", default=None,
                        help="Model cache directory (default: ./Models next to this script)")
    parser.add_argument("--diarize", action="store_true",
                        help="Assign speaker labels to segments and aligned words")
    parser.add_argument("--min_speakers", "--min-speakers", default=None,
                        help="Minimum number of speakers (positive integer)")
    parser.add_argument("--max_speakers", "--max-speakers", default=None,
                        help="Maximum number of speakers (positive integer)")
    parser.add_argument("--hf_token", "--hf-token", default=None,
                        help="HF token, remembered in project settings.json")
    parser.add_argument("--batch_size", "--batch-size", type=int, default=16,
                        help="Transcription batch size (default: 16)")
    parser.add_argument("--compute_type", "--compute-type", default=None,
                        choices=["int8", "float16", "float32", "int8_float16"])
    parser.add_argument("--output_dir", "--output-dir", default=None,
                        help="Output folder (default: the audio file's folder)")
    args = parser.parse_args(argv)
    if not os.path.isfile(args.audio):
        parser.error("Audio/video file does not exist.")
    if args.batch_size < 1:
        parser.error("Batch size must be a positive integer.")

    token = args.hf_token.strip() if args.hf_token else None

    def report(message):
        print(settings.redact_secrets(message, token, os.environ.get("HF_TOKEN")))

    if args.diarize:
        try:
            token = settings.resolve_hf_token(token)
        except settings.SettingsError as exc:
            report(f"Warning: {exc}")
            token = os.environ.get("HF_TOKEN", "").strip() or None
    try:
        minimum, maximum = pipeline.validate_diarization_options(
            args.diarize, args.min_speakers, args.max_speakers, token)
    except ValueError as exc:
        parser.error(str(exc))
    if args.hf_token is not None:
        try:
            settings.save_hf_token(args.hf_token)
        except settings.SettingsError as exc:
            report(f"Warning: {exc}")

    try:
        return _transcribe(args, token, minimum, maximum, report)
    except Exception as exc:
        report(f"ERROR: {exc}")
        return 1


def _transcribe(args, token, minimum, maximum, report):

    # Model cache directory
    if args.model_dir:
        model_dir = os.path.abspath(args.model_dir)
    else:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Models")
    os.makedirs(model_dir, exist_ok=True)
    os.environ["HF_HOME"] = model_dir

    # Device
    _, t_dev, a_dev = pipeline.detect_device(args.device)
    default_compute = "float16" if t_dev == "cuda" else "int8"
    compute, adjusted = pipeline.resolve_compute(t_dev, args.compute_type or default_compute)
    if adjusted:
        report("float16 not supported on CPU — using int8")
    report(f"Device: {t_dev.upper()}   Compute: {compute}")

    # Model
    report(f"Loading model '{args.model}'...")
    model = pipeline.load_model(args.model, t_dev, compute, args.language, beam=5)

    # Audio
    report("Loading audio...")
    audio = pipeline.load_audio(args.audio)

    # Transcribe
    report("Transcribing...")
    try:
        result, detected_lang = pipeline.transcribe(model, audio, args.batch_size, args.language)
    finally:
        del model
        pipeline.cleanup_memory()
    report(f"  Language: {detected_lang}   Segments: {len(result['segments'])}")

    # Align
    report("Aligning word timestamps...")
    try:
        result = pipeline.align(result, detected_lang, a_dev, audio)
    except Exception as e:
        report(f"  Warning: alignment failed ({e}) — continuing without word timestamps")
        if args.diarize:
            report("  Speaker labels will be assigned to segments only.")
        result.setdefault("language", detected_lang)

    if args.diarize:
        pipeline.cleanup_memory()
        d_dev = "cuda" if t_dev == "cuda" else "cpu"
        report(f"Diarizing... Device: {d_dev.upper()}")
        result = pipeline.diarize(
            result, audio, d_dev, token, minimum, maximum, model_dir)

    # Export
    out_dir = args.output_dir or os.path.dirname(os.path.abspath(args.audio))
    formats = list(pipeline.STANDARD_FORMATS) if args.output == "all" else [args.output]
    results = pipeline.export(result, formats, out_dir, args.audio, {})
    failed = False
    for fmt, path, err in results:
        if err:
            report(f"  {fmt} error: {err}")
            failed = True
        elif fmt == "word_json":
            import json
            with open(path, encoding="utf-8") as fh:
                words = json.load(fh)
            report(f"Done!  {len(words)} words → {path}")
        else:
            report(f"Done!  → {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

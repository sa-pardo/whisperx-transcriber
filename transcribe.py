"""
WhisperX Transcriber — headless CLI

Usage:
    python transcribe.py <audio_or_video_file> [options]

Options:
    --model      Model name (default: large-v2)
                 Choices: tiny, base, small, medium, large-v2, large-v3
    --language   Language code (default: auto-detect)
                 Examples: en, ar, fr, de, es, zh, ja
    --device     cuda | cpu (default: auto-detect)
    --output     Output format: word_json, srt, vtt, txt (default: word_json)
    --model-dir  Where to cache downloaded models (default: ./Models)

Examples:
    python transcribe.py audio.mp3
    python transcribe.py audio.mp3 --language en --model large-v2
    python transcribe.py audio.mp3 --device cpu --output srt
"""
import os
import sys
import json
import argparse


def detect_device():
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def main():
    parser = argparse.ArgumentParser(
        description="WhisperX headless transcription CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audio", help="Path to audio or video file")
    parser.add_argument("--model",     default="large-v2",
                        help="Whisper model (default: large-v2)")
    parser.add_argument("--language",  default=None,
                        help="Language code, e.g. en, ar, fr (default: auto-detect)")
    parser.add_argument("--device",    default=None,
                        help="cuda | cpu (default: auto-detect)")
    parser.add_argument("--output",    default="word_json",
                        choices=["word_json", "srt", "vtt", "txt", "tsv", "json"],
                        help="Output format (default: word_json)")
    parser.add_argument("--model-dir", default=None,
                        help="Model cache directory (default: ./Models next to this script)")
    args = parser.parse_args()

    # Resolve model cache directory
    if args.model_dir:
        model_dir = os.path.abspath(args.model_dir)
    else:
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Models")
    os.makedirs(model_dir, exist_ok=True)
    os.environ["HF_HOME"] = model_dir

    # Resolve device
    device = args.device or detect_device()
    compute = "float16" if device == "cuda" else "int8"
    print(f"Device : {device.upper()}   Compute: {compute}")

    import whisperx

    # Load model
    print(f"Loading model '{args.model}'...")
    model = whisperx.load_model(
        args.model, device,
        compute_type=compute,
        language=args.language,
    )

    # Load audio
    print("Loading audio...")
    audio = whisperx.load_audio(args.audio)

    # Transcribe
    print("Transcribing...")
    tx_kwargs = {}
    if args.language:
        tx_kwargs["language"] = args.language
    result = model.transcribe(audio, batch_size=16, **tx_kwargs)
    detected_lang = result.get("language", args.language or "?")
    print(f"  Language: {detected_lang}   Segments: {len(result['segments'])}")

    # Align word timestamps
    print("Aligning word timestamps...")
    try:
        align_device = "cpu" if device == "mps" else device
        model_a, meta = whisperx.load_align_model(
            language_code=detected_lang, device=align_device)
        result = whisperx.align(
            result["segments"], model_a, meta, audio, align_device)
    except Exception as e:
        print(f"  Warning: alignment failed ({e}) — continuing without word timestamps")

    # Save output
    base = os.path.splitext(args.audio)[0]
    out_dir = os.path.dirname(os.path.abspath(args.audio))

    if args.output == "word_json":
        words = [w for seg in result["segments"]
                 for w in seg.get("words", [])]
        out_path = base + "_words.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(words, fh, indent=2, ensure_ascii=False)
        print(f"Done!  {len(words)} words → {out_path}")
    else:
        from whisperx.utils import get_writer
        writer_opts = {"max_line_width": None, "max_line_count": None,
                       "highlight_words": False}
        get_writer(args.output, out_dir)(result, args.audio, writer_opts)
        print(f"Done!  → {base}.{args.output}")


if __name__ == "__main__":
    main()

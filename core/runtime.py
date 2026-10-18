"""Small dependency probe usable from either local Python launcher."""
import argparse
from importlib import import_module, metadata, util
import subprocess
import sys
import re
import traceback
import warnings


# Exit 1 is reserved for probe failures (including unhandled Python errors),
# not missing packages. The launcher may request setup only for exit 10.
EXIT_READY = 0
EXIT_NEEDS_SETUP = 10
EXIT_PROBE_ERROR = 1

SETUP_VERSION = "diarization-v1"
TORCH_VERSIONS = {"torch": "2.8.0", "torchaudio": "2.8.0", "torchvision": "0.23.0"}
ENGINE_VERSIONS = {"whisperx": "3.8.6", "pyannote.audio": "4.0.7", "torchcodec": "0.7.0"}


def has_nvidia() -> bool:
    try:
        kwargs = {"capture_output": True, "timeout": 6}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return subprocess.run(["nvidia-smi"], **kwargs).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def cuda_torch_index() -> str | None:
    """The pinned GPU wheels require a driver that supports CUDA 12.8."""
    try:
        kwargs = dict(capture_output=True, text=True, timeout=6)
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(["nvidia-smi"], **kwargs)
        # Newer drivers report "CUDA UMD Version" instead of "CUDA Version".
        match = re.search(r"CUDA(?: UMD)? Version:\s*(\d+)\.(\d+)", result.stdout)
        if result.returncode != 0 or match is None:
            return None
        version = tuple(map(int, match.groups()))
        return "https://download.pytorch.org/whl/cu128" if version >= (12, 8) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _versions_match(versions) -> bool:
    try:
        return all(metadata.version(name).split("+")[0] == expected
                   for name, expected in versions.items())
    except metadata.PackageNotFoundError:
        return False


def torch_ready(require_cuda=False, *, quick=False) -> bool:
    if not _versions_match(TORCH_VERSIONS):
        return False
    if quick:
        # Startup never loads native libraries, even when checking a CUDA tag.
        return not require_cuda or "+cu" in metadata.version("torch").lower()
    try:
        torch = import_module("torch")
        import_module("torchaudio")
        import_module("torchvision")
        # Validate CPU imports too. A wheel's metadata can survive missing or
        # corrupt DLLs. Driver availability is not a reason to reinstall.
        return not require_cuda or torch.version.cuda is not None
    except Exception:
        traceback.print_exc()
        return False


def dependencies_ready(require_cuda=False, *, quick=False) -> bool:
    if not (torch_ready(require_cuda, quick=quick) and _versions_match(ENGINE_VERSIONS)
            and all(util.find_spec(name) is not None
                    for name in ("customtkinter", "PIL", "imageio_ffmpeg"))):
        return False
    if quick:
        return True
    try:
        # Only imports used by this application's pipeline are mandatory.
        # WhisperX decodes files with FFmpeg and passes preloaded waveforms to
        # Pyannote. Its native TorchCodec file decoder is not needed here.
        with warnings.catch_warnings(record=True) as captured:
            warnings.filterwarnings(
                "always",
                message=r"\s*torchcodec is not installed correctly",
                category=UserWarning,
            )
            for name in ("whisperx", "pyannote.audio", "customtkinter",
                         "PIL.Image", "imageio_ffmpeg"):
                import_module(name)
    except Exception:
        traceback.print_exc()
        return False

    torchcodec_unavailable = False
    for warning in captured:
        if (issubclass(warning.category, UserWarning)
                and str(warning.message).strip().lower().startswith(
                    "torchcodec is not installed correctly"
                )):
            torchcodec_unavailable = True
        else:
            # Never hide warnings about unrelated dependencies.
            warnings.showwarning(warning.message, warning.category,
                                 warning.filename, warning.lineno)

    if torchcodec_unavailable:
        print(
            "WARNING: TorchCodec native audio decoding is unavailable. "
            "Pyannote file-based decoding may fail, but WhisperX Transcriber "
            "uses predecoded waveforms; continuing installation.",
            file=sys.stderr,
        )
    return True

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--torch-only", action="store_true")
    parser.add_argument("--quick", action="store_true",
                        help="Check package metadata without importing PyTorch.")
    parser.add_argument("--cuda-index", action="store_true",
                        help="Print the compatible CUDA wheel index, or an empty line.")
    args = parser.parse_args()
    if args.cuda_index:
        print(cuda_torch_index() or "")
        return 0
    try:
        ready = (torch_ready(args.cuda, quick=args.quick) if args.torch_only
                 else dependencies_ready(args.cuda, quick=args.quick))
    except Exception:
        # Metadata/read failures are inconclusive, not an installation verdict.
        traceback.print_exc()
        return EXIT_PROBE_ERROR
    return EXIT_READY if ready else EXIT_NEEDS_SETUP


if __name__ == "__main__":
    sys.exit(main())

"""Small dependency probe usable from either local Python launcher."""
import argparse
from importlib import metadata, util
import subprocess
import sys
import re


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
        match = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", result.stdout)
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


def torch_ready(require_cuda=False) -> bool:
    if not _versions_match(TORCH_VERSIONS):
        return False
    if require_cuda:
        try:
            import torch
            # An installed CUDA build with a driver problem needs a driver fix,
            # not repeated package downloads on every launch.
            return torch.version.cuda is not None
        except (ImportError, OSError):
            return False
    return True


def dependencies_ready(require_cuda=False) -> bool:
    return (torch_ready(require_cuda) and _versions_match(ENGINE_VERSIONS)
            and all(util.find_spec(name) is not None
                    for name in ("customtkinter", "PIL", "imageio_ffmpeg")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--torch-only", action="store_true")
    parser.add_argument("--cuda-index", action="store_true",
                        help="Print the compatible CUDA wheel index, or an empty line.")
    args = parser.parse_args()
    if args.cuda_index:
        print(cuda_torch_index() or "")
        return 0
    ready = torch_ready(args.cuda) if args.torch_only else dependencies_ready(args.cuda)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())

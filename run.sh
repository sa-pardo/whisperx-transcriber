#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  WhisperX Transcriber — macOS / Linux launcher
#
#  First run  : creates .venv and installs all dependencies (5–20 min)
#  Later runs : opens the app in ~2 seconds
#
#  Requirements: Python 3.10+   brew install python  |  sudo apt install python3
#               Portable FFmpeg is installed with the core dependencies.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"
APP="$DIR/app.py"

echo ""
echo "  +------------------------------------------+"
echo "  |         WhisperX  Transcriber            |"
echo "  |         AI Transcription  by Muqaddimah  |"
echo "  +------------------------------------------+"
echo ""

# ── Verify app.py exists ──────────────────────────────────────────────────────
if [ ! -f "$APP" ]; then
    echo "  ERROR: app.py not found in $DIR"
    echo "  Make sure run.sh is in the same folder as app.py."
    echo ""
    exit 1
fi

# ── Find Python 3.10+ ─────────────────────────────────────────────────────────
echo "  Checking Python..."
PYTHON=""
for cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver="$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")"
        major="${ver%%.*}"
        minor="${ver#*.}"
        if [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 10 ] 2>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo "  Python 3.10+ not found."
    echo ""
    echo "  macOS:  brew install python"
    echo "  Ubuntu: sudo apt install python3.11"
    echo "  Other:  https://www.python.org/downloads/"
    echo ""
    exit 1
fi
echo "  Found $($PYTHON --version)"

# ── Select requirements using the shared driver compatibility check ──────────
UNAME="$(uname -s)"
ARCH="$(uname -m)"
RUNTIME_PYTHON="$PYTHON"
if [ -f "$VENV/bin/python" ]; then
    RUNTIME_PYTHON="$VENV/bin/python"
fi
TORCH_REQUIREMENTS="$DIR/requirements-cpu.txt"
CUDA_INDEX=""
CUDA_CHECK=()
if [ "$UNAME" = "Linux" ]; then
    CUDA_INDEX="$("$RUNTIME_PYTHON" "$DIR/core/runtime.py" --cuda-index)"
    if [ -n "$CUDA_INDEX" ]; then
        TORCH_REQUIREMENTS="$DIR/requirements-gpu.txt"
        CUDA_CHECK=(--cuda)
    fi
fi

# ── Skip setup if venv already ready ─────────────────────────────────────────
if [ -f "$VENV/bin/python" ]; then
    if "$VENV/bin/python" "$DIR/core/runtime.py" "${CUDA_CHECK[@]}"; then
        echo "  Environment ready."
        "$VENV/bin/python" "$APP"
        exit $?
    fi
fi

# ═════════════════════════════════════════════════════════════════════════════
echo ""
echo "  First-time setup — please wait, this takes a few minutes."
echo "  Your internet connection is needed to download packages."
echo ""
# ═════════════════════════════════════════════════════════════════════════════

# ── Create virtual environment ────────────────────────────────────────────────
echo "  [1/4] Creating virtual environment..."
if [ ! -f "$VENV/bin/python" ]; then
    "$PYTHON" -m venv "$VENV"
fi
echo "         Done."

# ── Upgrade pip ───────────────────────────────────────────────────────────────
echo "  [2/4] Upgrading pip..."
"$VENV/bin/pip" install --upgrade pip --quiet
echo "         Done."

# ── Install PyTorch from the selected requirements ──────────────────────────
echo "  [3/4] Installing PyTorch..."

if [ "$UNAME" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    echo "         Apple Silicon (M-series) — MPS acceleration available"
    # Standard PyTorch build has MPS support on Apple Silicon
elif [ -n "$CUDA_INDEX" ]; then
    echo "         NVIDIA GPU detected — installing CUDA 12.8 build"
    echo "         (This download is ~2.5 GB, please be patient)"
elif [ "$UNAME" = "Linux" ] && command -v nvidia-smi &>/dev/null; then
    echo "         CUDA 12.8 not detected — installing CPU build; check the NVIDIA driver"
else
    echo "         Installing CPU build"
fi

"$VENV/bin/pip" install --force-reinstall --no-deps -r "$TORCH_REQUIREMENTS" --quiet
echo "         Done."

# ── Install remaining packages ────────────────────────────────────────────────
echo "  [4/4] Installing WhisperX + UI dependencies..."
echo "         (Another ~500 MB — almost there)"
"$VENV/bin/pip" install -r "$DIR/requirements-core.txt" --quiet
echo "         Done."

# ── Verify the installed dependencies and selected PyTorch build ─────────────
echo ""
"$VENV/bin/python" "$DIR/core/runtime.py" "${CUDA_CHECK[@]}"

echo ""
echo "  Setup complete!  The app will open now and on every future run."
echo ""

# ── Launch ───────────────────────────────────────────────────────────────────
echo "  Launching WhisperX Transcriber..."
echo ""
"$VENV/bin/python" "$APP"

"""
WhisperX Transcriber — thin entry point.

On first launch:  shows setup_wizard.py to install the AI backend.
On later launches: checks for runtime/.setup_complete, then spawns
                   runtime/Scripts/python.exe app.py and exits.

This file and its PyInstaller bundle intentionally contain NO torch,
whisperx, ctranslate2, or any ML package — they download on first run.
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime
from enum import Enum
from core.runtime import EXIT_NEEDS_SETUP, EXIT_READY, SETUP_VERSION


def _base_dir() -> str:
    """Directory that contains (or will contain) runtime/ and app.py."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _runtime_python() -> str:
    base = _base_dir()
    pythonw = os.path.join(base, "runtime", "Scripts", "pythonw.exe")
    python  = os.path.join(base, "runtime", "Scripts", "python.exe")
    return pythonw if os.path.isfile(pythonw) else python


class RuntimeStatus(Enum):
    READY = "ready"
    NEEDS_SETUP = "needs_setup"
    UNVERIFIED = "unverified"


def _runtime_status() -> tuple[RuntimeStatus, str]:
    """Classify the local installation without importing PyTorch on startup.

    The full CUDA/import check runs when the setup wizard installs packages.
    A slow or failed quick probe is inconclusive, not proof that the
    installation is broken: try launching rather than reinstalling it.
    """
    base = _base_dir()
    py = os.path.join(base, "runtime", "Scripts", "python.exe")
    if not os.path.isfile(py):
        return RuntimeStatus.NEEDS_SETUP, "Local Python runtime is missing."

    flag = os.path.join(base, "runtime", ".setup_complete")
    if not os.path.isfile(flag):
        return RuntimeStatus.NEEDS_SETUP, "Installation completion marker is missing."
    try:
        with open(flag, encoding="utf-8") as fh:
            version = fh.read().strip()
    except OSError as exc:
        return RuntimeStatus.UNVERIFIED, f"Could not read the setup marker: {exc}"
    if version != SETUP_VERSION:
        return RuntimeStatus.NEEDS_SETUP, "Installed runtime needs an update."

    ffmpeg_binaries = os.path.join(
        base, "runtime", "Lib", "site-packages", "imageio_ffmpeg", "binaries"
    )
    if not os.path.isdir(ffmpeg_binaries) and not shutil.which("ffmpeg"):
        return RuntimeStatus.NEEDS_SETUP, "FFmpeg is missing."

    probe = os.path.join(base, "core", "runtime.py")
    if not os.path.isfile(probe):
        return RuntimeStatus.UNVERIFIED, "Dependency check script is missing."

    kwargs = dict(capture_output=True, timeout=12)
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        # --quick checks installed package metadata only. Do not call
        # nvidia-smi or import torch during the regular GUI launch.
        result = subprocess.run([py, probe, "--quick"], **kwargs)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return RuntimeStatus.UNVERIFIED, f"Quick dependency check unavailable: {exc}"

    if result.returncode == EXIT_READY:
        return RuntimeStatus.READY, ""
    if result.returncode == EXIT_NEEDS_SETUP:
        return RuntimeStatus.NEEDS_SETUP, "Required dependency versions are missing."
    reason = f"Dependency check exited unexpectedly with code {result.returncode}."
    if result.stderr:
        # Keep the traceback, including undecodable native output, for diagnosis.
        reason += "\n" + result.stderr.decode("utf-8", errors="replace").strip()
    return RuntimeStatus.UNVERIFIED, reason


def _log_startup_warning(message: str) -> None:
    """Keep the reason for an inconclusive probe without blocking startup."""
    try:
        path = os.path.join(_base_dir(), "startup-warning.log")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().astimezone().isoformat()} {message}\n")
    except OSError:
        pass  # Logging must never prevent the application from opening.


def _launch_app() -> None:
    """Replace this process with runtime/python app.py."""
    base = _base_dir()
    runtime_py = _runtime_python()
    app_script = os.path.join(base, "app.py")
    bootstrap_script = os.path.join(base, "app_bootstrap.py")

    if not os.path.isfile(app_script):
        _fatal(f"app.py not found at:\n{app_script}\n\nReinstall the application.")

    if not os.path.isfile(bootstrap_script):
        _fatal(f"app_bootstrap.py not found at:\n{bootstrap_script}\n\nReinstall the application.")

    if not os.path.isfile(runtime_py):
        _fatal("Runtime Python not found. Run the app again to reinstall the backend.")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    # PyInstaller's Tkinter hook sets these to its bundled Tcl/Tk data.
    # The separately installed runtime Python must use its own Tcl/Tk version.
    if getattr(sys, "frozen", False):
        env.pop("TCL_LIBRARY", None)
        env.pop("TK_LIBRARY", None)

    # Prepend bundled ffmpeg binaries to PATH so whisperx.load_audio can find ffmpeg
    ffmpeg_bin = os.path.join(base, "runtime", "Lib", "site-packages",
                              "imageio_ffmpeg", "binaries")
    if os.path.isdir(ffmpeg_bin):
        env["PATH"] = ffmpeg_bin + os.pathsep + env.get("PATH", "")

    try:
        subprocess.Popen(
            [runtime_py, bootstrap_script],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        _fatal(f"Unable to launch the application: {exc}")
    sys.exit(0)


def _fatal(msg: str) -> None:
    """Show an error dialog then exit."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("WhisperX Transcriber", msg)
        root.destroy()
    except Exception:
        print("FATAL:", msg, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    repair = "--repair" in sys.argv[1:]
    if repair:
        status, reason = RuntimeStatus.NEEDS_SETUP, "Repair requested by user."
    else:
        status, reason = _runtime_status()
    if status is RuntimeStatus.UNVERIFIED:
        _log_startup_warning(reason)
    if status is not RuntimeStatus.NEEDS_SETUP:
        _launch_app()
        return

    try:
        from setup_wizard import SetupWizard
    except ImportError as exc:
        _fatal(f"Cannot load setup wizard: {exc}")
    wizard = SetupWizard(
        base_dir=_base_dir(), on_complete=_launch_app, reason=reason, repair=repair
    )
    wizard.run()


if __name__ == "__main__":
    main()

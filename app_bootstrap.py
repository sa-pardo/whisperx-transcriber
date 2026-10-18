"""Run the GUI using the local Python runtime and report startup errors.

The thin launcher runs pythonw.exe without a console. Unhandled import errors
would otherwise make the application disappear without explaining the failure.
"""
import os
import runpy
import subprocess
import sys
import traceback
from datetime import datetime


def _show_error(message: str) -> bool:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno(
                "WhisperX Transcriber",
                message + "\n\nOpen the repair wizard now?",
            )
        finally:
            root.destroy()
    except Exception:
        print(message, file=sys.stderr)
    return False


def _report_startup_error(exc: Exception) -> None:
    base = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base, "startup-error.log")
    error_trace = traceback.format_exc()
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\n[{datetime.now().astimezone().isoformat()}]\n{error_trace}\n")
        detail = f"See the error log at:\n{log_path}"
    except OSError:
        detail = "Unable to write the startup error log."

    if _show_error(
        f"WhisperX Transcriber could not start.\n\n"
        f"{type(exc).__name__}: {exc}\n\n{detail}"
    ):
        exe = os.path.join(base, "WhisperXTranscriber.exe")
        try:
            subprocess.Popen([exe, "--repair"])
        except OSError as launch_error:
            _show_error(f"Unable to open the repair wizard: {launch_error}")


def main() -> int:
    app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    try:
        runpy.run_path(app_script, run_name="__main__")
        return 0
    except Exception as exc:
        _report_startup_error(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

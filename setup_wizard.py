"""
WhisperX Transcriber — first-run setup wizard.

Downloads and installs the AI backend (torch + whisperx) into a local
runtime/ venv on first launch. Uses ONLY stdlib + customtkinter + tkinter
so it can run from the thin PyInstaller launcher without any ML packages.
"""
import os
import sys
import queue
import shutil
import subprocess
import threading
import webbrowser
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


_F  = lambda sz, wt="normal": ctk.CTkFont(family="Segoe UI", size=sz, weight=wt)
_FM = lambda sz=10: ctk.CTkFont(family="Consolas", size=sz)

# Colours (dark, light) tuples
_BG    = ("#f5f5f5", "#161616")
_HDR   = ("#111111", "#0d0d0d")
_CARD  = ("#ffffff", "#1e1e1e")
_FTR   = ("#e8e8e8", "#111111")
_PRI   = ("#111111", "#ffffff")
_DIM   = ("#555555", "#888888")
_HINT  = ("#888888", "#555555")
_LOG   = ("#f0f0f0", "#0d0d0d")
_LTXT  = ("#333333", "#aaaaaa")


# ── Detection helpers ─────────────────────────────────────────────────────────

def _has_nvidia() -> bool:
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, timeout=6)
        return r.returncode == 0
    except Exception:
        return False


def _find_python() -> str | None:
    """Return path to system Python 3.10+, or None."""
    candidates = ["python", "python3", "python3.13", "python3.12",
                  "python3.11", "python3.10"]
    for cmd in candidates:
        path = shutil.which(cmd)
        if not path:
            continue
        try:
            r = subprocess.run([path, "--version"], capture_output=True,
                               text=True, timeout=5)
            out = (r.stdout + r.stderr).strip()
            for minor in ["3.10", "3.11", "3.12", "3.13"]:
                if minor in out:
                    return path
        except Exception:
            continue
    return None


# ── Wizard ────────────────────────────────────────────────────────────────────

class SetupWizard:
    def __init__(self, base_dir: str, on_complete):
        self.base_dir    = base_dir
        self.on_complete = on_complete
        self.runtime_dir = os.path.join(base_dir, "runtime")
        self.has_gpu     = _has_nvidia()
        self.python_path = _find_python()
        self._q: queue.Queue[tuple[str, str]] = queue.Queue()

        self.win = ctk.CTk()
        self.win.title("WhisperX Transcriber — Setup")
        self.win.geometry("620x540")
        self.win.resizable(False, False)
        self.win.grid_columnconfigure(0, weight=1)
        self.win.grid_rowconfigure(0, weight=1)

        self._build_shell()
        self._show_welcome()
        self.win.after(100, self._drain_log)

    # ── Shell (header + swappable content + footer) ───────────────────────────

    def _build_shell(self):
        root = ctk.CTkFrame(self.win, fg_color=_BG, corner_radius=0)
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(root, fg_color=_HDR, corner_radius=0, height=84)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="WhisperX Transcriber", font=_F(20, "bold"),
                     text_color="#ffffff").grid(row=0, column=0, pady=(20, 2))
        ctk.CTkLabel(hdr, text="First-time Setup", font=_F(12),
                     text_color="#666666").grid(row=1, column=0, pady=(0, 16))

        # Content (swappable)
        self.body = ctk.CTkFrame(root, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=32, pady=22)
        self.body.grid_columnconfigure(0, weight=1)

        # Footer
        self.ftr = ctk.CTkFrame(root, fg_color=_FTR, corner_radius=0, height=66)
        self.ftr.grid(row=2, column=0, sticky="ew")
        self.ftr.grid_propagate(False)
        self.ftr.grid_columnconfigure(0, weight=1)

    def _clear(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    # ── Page 1: Welcome ───────────────────────────────────────────────────────

    def _show_welcome(self):
        self._clear(self.body)
        self._clear(self.ftr)
        b = self.body

        ctk.CTkLabel(b, text="Welcome", font=_F(22, "bold"),
                     text_color=_PRI).grid(row=0, column=0, sticky="w", pady=(0, 6))
        ctk.CTkLabel(b,
                     text=("This wizard installs the AI transcription engine.\n"
                            "This is a one-time 1–3 GB download (2–5 GB on disk).\n"
                            "Subsequent launches open instantly."),
                     font=_F(13), text_color=_DIM,
                     wraplength=500, justify="left",
                     ).grid(row=1, column=0, sticky="w", pady=(0, 18))

        # GPU card
        gcard = ctk.CTkFrame(b, fg_color=_CARD, corner_radius=10)
        gcard.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        gcard.grid_columnconfigure(0, weight=1)

        gpu_label = ("●  NVIDIA GPU detected — GPU acceleration will be used"
                     if self.has_gpu else "●  No GPU detected — will run on CPU")
        gpu_color = "#22cc66" if self.has_gpu else "#888888"
        ctk.CTkLabel(gcard, text=gpu_label, font=_F(12, "bold"),
                     text_color=gpu_color).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        # Python card
        pcard = ctk.CTkFrame(b, fg_color=_CARD, corner_radius=10)
        pcard.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        pcard.grid_columnconfigure(0, weight=1)

        if self.python_path:
            py_text  = f"●  Python found: {self.python_path}"
            py_color = "#22cc66"
        else:
            py_text  = "●  Python 3.10+ not found — required for setup"
            py_color = "#ff4d4d"

        ctk.CTkLabel(pcard, text=py_text, font=_F(11),
                     text_color=py_color).grid(row=0, column=0, padx=16, pady=10, sticky="w")

        if not self.python_path:
            ctk.CTkLabel(pcard,
                         text="Install Python 3.10+ from python.org — tick 'Add Python to PATH'",
                         font=_F(10), text_color=_HINT,
                         ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # Footer
        if self.python_path:
            ctk.CTkButton(self.ftr, text="Begin Setup →", width=160, height=40,
                          font=_F(13, "bold"), fg_color="#4a9eff", hover_color="#6ab0ff",
                          command=self._start_install,
                          ).grid(row=0, column=0, pady=13, padx=18, sticky="e")
        else:
            ctk.CTkButton(self.ftr, text="Download Python →", width=180, height=40,
                          font=_F(13), fg_color="#4a9eff", hover_color="#6ab0ff",
                          command=lambda: webbrowser.open(
                              "https://www.python.org/downloads/"),
                          ).grid(row=0, column=0, pady=13, padx=18, sticky="e")


    # ── Page 2: Installing ────────────────────────────────────────────────────

    def _show_installing(self):
        self._clear(self.body)
        self._clear(self.ftr)
        b = self.body
        b.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(b, text="Installing...", font=_F(22, "bold"),
                     text_color=_PRI).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._status_var = ctk.StringVar(value="Preparing...")
        ctk.CTkLabel(b, textvariable=self._status_var, font=_F(12),
                     text_color=_DIM).grid(row=1, column=0, sticky="w", pady=(0, 8))

        prog_row = ctk.CTkFrame(b, fg_color="transparent")
        prog_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        prog_row.grid_columnconfigure(0, weight=1)

        self._prog = ctk.CTkProgressBar(prog_row, height=8, corner_radius=4,
                                         fg_color=("#d0d0d0", "#1a1a1a"),
                                         progress_color="#4a9eff",
                                         mode="determinate")
        self._prog.set(0)
        self._prog.grid(row=0, column=0, sticky="ew")

        self._pct_lbl = ctk.CTkLabel(prog_row, text="0%", font=_F(10),
                                      text_color=_HINT, width=36)
        self._pct_lbl.grid(row=0, column=1, padx=(8, 0))

        self._activity_lbl = ctk.CTkLabel(b, text="", font=_FM(9),
                                           text_color=_HINT, anchor="w",
                                           wraplength=540)
        self._activity_lbl.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        self._log_box = ctk.CTkTextbox(b, font=_FM(10), fg_color=_LOG,
                                        text_color=_LTXT, corner_radius=8,
                                        state="disabled")
        self._log_box.grid(row=4, column=0, sticky="nsew")

        ctk.CTkLabel(self.ftr,
                     text="Please wait — typically 10–45 minutes depending on your connection speed.",
                     font=_F(11), text_color=_HINT,
                     ).grid(row=0, column=0, pady=18, padx=18)

    def _drain_log(self):
        while True:
            try:
                kind, text = self._q.get_nowait()
                if kind == "r":
                    if hasattr(self, "_activity_lbl"):
                        t = text.strip()[:90]
                        self.win.after(0, lambda s=t: self._activity_lbl.configure(text=s))
                else:
                    if hasattr(self, "_log_box") and text:
                        if "━" in text or "─" in text:
                            continue
                        self._log_box.configure(state="normal")
                        self._log_box.insert("end", text + "\n")
                        self._log_box.see("end")
                        self._log_box.configure(state="disabled")
            except queue.Empty:
                break
        self.win.after(100, self._drain_log)

    def _log(self, msg: str):
        self._q.put(("n", msg))

    def _set_status(self, msg: str):
        if hasattr(self, "_status_var"):
            self.win.after(0, lambda: self._status_var.set(msg))
        if hasattr(self, "_activity_lbl"):
            self.win.after(0, lambda: self._activity_lbl.configure(text=""))

    def _set_progress(self, value: float, step: str = ""):
        def _do():
            if hasattr(self, "_prog"):
                self._prog.set(max(0.0, min(1.0, value)))
            if hasattr(self, "_pct_lbl"):
                self._pct_lbl.configure(text=f"{int(value * 100)}%")
        self.win.after(0, _do)

    def _animate_progress(self, current: float, target: float):
        """Slowly drift the progress bar toward target while install is running."""
        if getattr(self, "_install_done", False):
            return
        next_val = min(current + 0.005, target)
        self._set_progress(next_val)
        if next_val < target:
            self.win.after(1000, lambda: self._animate_progress(next_val, target))

    # ── Install logic ─────────────────────────────────────────────────────────

    def _start_install(self):
        self._show_installing()
        threading.Thread(target=self._run_install, daemon=True).start()

    def _pkg_installed(self, venv_pip: str, pkg: str) -> bool:
        r = subprocess.run(
            [venv_pip, "show", pkg],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return r.returncode == 0

    def _run_pip(self, cmd: list[str]) -> int:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        buf = ""
        while True:
            chunk = proc.stdout.read(128)
            if not chunk:
                break
            for ch in chunk.decode("utf-8", errors="replace"):
                if ch == "\r":
                    if buf.strip():
                        self._q.put(("r", buf))
                    buf = ""
                elif ch == "\n":
                    if buf.strip():
                        self._q.put(("n", buf.rstrip()))
                    buf = ""
                else:
                    buf += ch
        if buf.strip():
            self._q.put(("n", buf.rstrip()))
        proc.wait()
        return proc.returncode

    def _run_install(self):
        try:
            py      = self.python_path
            runtime = self.runtime_dir
            venv_py  = os.path.join(runtime, "Scripts", "python.exe")
            venv_pip = os.path.join(runtime, "Scripts", "pip.exe")

            # 1. Create venv (skip if already exists)
            if not os.path.isfile(venv_py):
                self._set_status("Creating virtual environment...")
                self._log(f"Creating venv at: {runtime}\n")
                r = subprocess.run([py, "-m", "venv", runtime],
                                   capture_output=True, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                if r.returncode != 0:
                    raise RuntimeError(f"venv creation failed:\n{r.stderr}")
            else:
                self._log(f"Venv already exists, reusing: {runtime}\n")
            self._set_progress(0.05)

            # 2. Upgrade pip
            self._set_status("Upgrading pip...")
            self._log("\n[pip] Upgrading...")
            self._run_pip([venv_py, "-m", "pip", "install",
                           "--upgrade", "pip", "--quiet", "--timeout", "120"])
            self._set_progress(0.10)

            # 3. Install everything in one pass — whisperx pulls the correct
            #    torch version directly, avoiding a redundant download.
            if self._pkg_installed(venv_pip, "whisperx"):
                self._log("\n[All packages] Already installed — skipping.")
                self._set_progress(0.95)
            else:
                self._set_status("Downloading AI engine and dependencies (1–3 GB, up to 5 GB on disk)...")
                self._log("\n[Installing] whisperx + torch + all dependencies...")
                self._install_done = False
                self.win.after(1000, lambda: self._animate_progress(0.10, 0.89))
                rc = self._run_pip([venv_pip, "install",
                                    "--timeout", "120",
                                    "whisperx",
                                    "customtkinter>=5.2.2",
                                    "Pillow"])
                self._install_done = True
                if rc != 0:
                    raise RuntimeError(
                        "pip install failed — see the log above for details.")
                self._set_progress(0.95)

            # 5. Mark complete
            flag = os.path.join(runtime, ".setup_complete")
            with open(flag, "w") as fh:
                fh.write("ok")

            self._set_progress(1.0)
            self._set_status("Setup complete!")
            self._log("\n✓ All done! Launching app...")
            self.win.after(800, self._show_done)

        except Exception as exc:
            import traceback as tb
            self._log(f"\nERROR: {exc}\n{tb.format_exc()}")
            self._set_status("Setup failed — see log above")
            self.win.after(0, lambda: self._show_error(str(exc)))

    # ── Page 3: Done / Error ──────────────────────────────────────────────────

    def _show_done(self):
        if hasattr(self, "_prog"):
            self._prog.stop()
        self._clear(self.body)
        self._clear(self.ftr)
        b = self.body

        ctk.CTkLabel(b, text="Setup Complete", font=_F(22, "bold"),
                     text_color="#22cc66").grid(row=0, column=0, sticky="w", pady=(0, 12))
        ctk.CTkLabel(b,
                     text=("The AI transcription engine is installed.\n\n"
                            "Click Launch to open WhisperX Transcriber.\n"
                            "Future launches will skip this screen and open instantly."),
                     font=_F(13), text_color=_DIM,
                     wraplength=500, justify="left",
                     ).grid(row=1, column=0, sticky="w")

        ctk.CTkButton(self.ftr, text="Launch App", width=160, height=40,
                      font=_F(13, "bold"), fg_color="#22cc66", hover_color="#2de07a",
                      text_color="#ffffff",
                      command=self._finish,
                      ).grid(row=0, column=0, pady=13, padx=18, sticky="e")

    def _show_error(self, msg: str):
        if hasattr(self, "_prog"):
            try:
                self._prog.stop()
            except Exception:
                pass
        self._clear(self.ftr)
        ctk.CTkLabel(self.ftr, text=f"Error: {msg[:100]}",
                     font=_F(11), text_color="#ff4d4d",
                     wraplength=550,
                     ).grid(row=0, column=0, pady=10, padx=18)
        ctk.CTkButton(self.ftr, text="Retry", width=90, height=36,
                      font=_F(12), fg_color=("#d0d0d0", "#2a2a2a"),
                      hover_color=("#c0c0c0", "#3a3a3a"),
                      command=self._retry,
                      ).grid(row=0, column=1, pady=10, padx=(0, 18))

    def _retry(self):
        self._show_welcome()

    def _finish(self):
        self.win.destroy()
        self.on_complete()

    def run(self):
        self.win.mainloop()

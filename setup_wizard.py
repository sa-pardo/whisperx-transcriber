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

TORCH_CPU_URL = "https://download.pytorch.org/whl/cpu"
TORCH_GPU_URL = "https://download.pytorch.org/whl/cu121"

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
        self.use_gpu     = self.has_gpu
        self.python_path = _find_python()
        self._q: queue.Queue[str] = queue.Queue()

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
                            "It is a one-time download. Subsequent launches open instantly."),
                     font=_F(13), text_color=_DIM,
                     wraplength=500, justify="left",
                     ).grid(row=1, column=0, sticky="w", pady=(0, 18))

        # GPU card
        gcard = ctk.CTkFrame(b, fg_color=_CARD, corner_radius=10)
        gcard.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        gcard.grid_columnconfigure(1, weight=1)

        gpu_label = ("●  NVIDIA GPU detected" if self.has_gpu
                     else "●  No GPU detected — CPU mode")
        gpu_color = "#22cc66" if self.has_gpu else "#888888"
        ctk.CTkLabel(gcard, text=gpu_label, font=_F(12, "bold"),
                     text_color=gpu_color).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self._size_lbl = ctk.CTkLabel(gcard,
                                       text=self._size_hint(),
                                       font=_F(11), text_color=_HINT)
        self._size_lbl.grid(row=0, column=1, padx=16, pady=12, sticky="e")

        if self.has_gpu:
            tr = ctk.CTkFrame(gcard, fg_color="transparent")
            tr.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
            tr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(tr, text="Use GPU acceleration  (recommended — ~10× faster)",
                         font=_F(12), text_color=_DIM).grid(row=0, column=0, sticky="w")
            self._gpu_sw = ctk.CTkSwitch(tr, text="", width=44,
                                          button_color="#4a9eff",
                                          progress_color="#4a9eff",
                                          command=self._on_gpu_toggle)
            self._gpu_sw.grid(row=0, column=1)
            self._gpu_sw.select()

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

    def _size_hint(self) -> str:
        return "~3 GB download" if self.use_gpu else "~700 MB download"

    def _on_gpu_toggle(self):
        self.use_gpu = bool(self._gpu_sw.get())
        self._size_lbl.configure(text=self._size_hint())

    # ── Page 2: Installing ────────────────────────────────────────────────────

    def _show_installing(self):
        self._clear(self.body)
        self._clear(self.ftr)
        b = self.body
        b.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(b, text="Installing...", font=_F(22, "bold"),
                     text_color=_PRI).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._status_var = ctk.StringVar(value="Preparing...")
        ctk.CTkLabel(b, textvariable=self._status_var, font=_F(12),
                     text_color=_DIM).grid(row=1, column=0, sticky="w", pady=(0, 12))

        self._prog = ctk.CTkProgressBar(b, height=5, corner_radius=3,
                                         fg_color=("#d0d0d0", "#1a1a1a"),
                                         progress_color="#4a9eff",
                                         mode="indeterminate")
        self._prog.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        self._prog.start()

        self._log_box = ctk.CTkTextbox(b, font=_FM(10), fg_color=_LOG,
                                        text_color=_LTXT, corner_radius=8,
                                        state="disabled")
        self._log_box.grid(row=3, column=0, sticky="nsew")

        ctk.CTkLabel(self.ftr,
                     text="Please wait — 5 to 30 minutes depending on your connection.",
                     font=_F(11), text_color=_HINT,
                     ).grid(row=0, column=0, pady=18, padx=18)

    def _drain_log(self):
        while True:
            try:
                msg = self._q.get_nowait()
                if hasattr(self, "_log_box"):
                    self._log_box.configure(state="normal")
                    self._log_box.insert("end", msg + "\n")
                    self._log_box.see("end")
                    self._log_box.configure(state="disabled")
            except queue.Empty:
                break
        self.win.after(100, self._drain_log)

    def _log(self, msg: str):
        self._q.put(msg)

    def _set_status(self, msg: str):
        if hasattr(self, "_status_var"):
            self.win.after(0, lambda: self._status_var.set(msg))

    # ── Install logic ─────────────────────────────────────────────────────────

    def _start_install(self):
        self._show_installing()
        threading.Thread(target=self._run_install, daemon=True).start()

    def _run_pip(self, cmd: list[str]) -> int:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, errors="replace",
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                self._log(line)
        proc.wait()
        return proc.returncode

    def _run_install(self):
        try:
            py      = self.python_path
            runtime = self.runtime_dir
            venv_py  = os.path.join(runtime, "Scripts", "python.exe")
            venv_pip = os.path.join(runtime, "Scripts", "pip.exe")

            # 1. Create venv
            self._set_status("Creating virtual environment...")
            self._log(f"Creating venv at: {runtime}\n")
            r = subprocess.run([py, "-m", "venv", runtime],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"venv creation failed:\n{r.stderr}")

            # 2. Upgrade pip
            self._set_status("Upgrading pip...")
            self._log("\n[pip] Upgrading...")
            self._run_pip([venv_py, "-m", "pip", "install",
                           "--upgrade", "pip", "--quiet"])

            # 3. PyTorch
            torch_idx = TORCH_GPU_URL if self.use_gpu else TORCH_CPU_URL
            size_hint = "~3 GB" if self.use_gpu else "~700 MB"
            self._set_status(f"Downloading PyTorch ({size_hint})...")
            self._log(f"\n[PyTorch] Installing from {torch_idx}")
            rc = self._run_pip([venv_pip, "install",
                                "torch", "torchaudio",
                                "--index-url", torch_idx])
            if rc != 0:
                raise RuntimeError("PyTorch install failed — check your internet connection.")

            # 4. WhisperX + UI deps
            self._set_status("Installing WhisperX and UI dependencies...")
            self._log("\n[WhisperX + UI] Installing...")
            rc = self._run_pip([venv_pip, "install",
                                "whisperx",
                                "customtkinter>=5.2.2",
                                "Pillow"])
            if rc != 0:
                raise RuntimeError("WhisperX install failed.")

            # 5. Mark complete
            flag = os.path.join(runtime, ".setup_complete")
            with open(flag, "w") as fh:
                fh.write("ok")

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
        import shutil as sh
        # Clean up partial runtime before retrying
        if os.path.isdir(self.runtime_dir):
            sh.rmtree(self.runtime_dir, ignore_errors=True)
        self._show_welcome()

    def _finish(self):
        self.win.destroy()
        self.on_complete()

    def run(self):
        self.win.mainloop()

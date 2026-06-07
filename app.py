import os
import sys
import json
import queue
import threading
import traceback
import subprocess
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

if IS_WIN:
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Muqaddimah.WhisperXTranscriber")
    except Exception:
        pass

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Color palette — (light, dark) ────────────────────────────────────────────
_SB      = ("#f5f5f5", "#111111")
_CARD    = ("#ffffff", "#1e1e1e")
_CONT    = ("#f0f0f0", "#161616")
_ENTRY   = ("#f8f8f8", "#141414")
_BAR     = ("#e8e8e8", "#0d0d0d")
_SEP     = ("#d8d8d8", "#1e1e1e")
_FMT     = ("#ececec", "#161616")
_LOGHDR  = ("#e0e0e0", "#111111")
_NAVACT  = ("#e5e5e5", "#1e1e1e")
_NAVHOV  = ("#ebebeb", "#1a1a1a")
_MID     = ("#d8d8d8", "#2a2a2a")
_MIDHOV  = ("#c8c8c8", "#3a3a3a")
_BORDER  = ("#d8d8d8", "#2a2a2a")
_SCRL_B  = ("#c8c8c8", "#2a2a2a")
_SCRL_H  = ("#b8b8b8", "#3a3a3a")
_PROG_BG = ("#d0d0d0", "#1a1a1a")
_MAC_BG  = ("#e8f5e8", "#162016")
_DROP    = ("#f0f0f0", "#1e1e1e")

_PRI     = ("#111111", "#ffffff")
_LOGO_S  = ("#888888", "#888888")
_NAV_OF  = ("#777777", "#666666")
_LABEL   = ("#444444", "#888888")
_HINT    = ("#999999", "#666666")
_SECHI   = ("#777777", "#666666")
_STAT    = ("#444444", "#888888")
_LOG_H   = ("#555555", "#666666")
_LOG_B   = ("#111111", "#c0c0c0")
_FMT_N   = ("#111111", "#dddddd")
_FMT_D   = ("#666666", "#777777")
_TOGG_L  = ("#333333", "#cccccc")
_DIM_TXT = ("#999999", "#888888")
_MAC_TXT = ("#2a7a2a", "#3a7a3a")


# ── Fonts ─────────────────────────────────────────────────────────────────────
def F(size=13, weight="normal"):
    family = "SF Pro Display" if IS_MAC else "Segoe UI"
    return ctk.CTkFont(family=family, size=size, weight=weight)

def FM(size=10):
    family = "Menlo" if IS_MAC else "Consolas"
    return ctk.CTkFont(family=family, size=size)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _default_model_dir():
    if getattr(sys, "frozen", False):
        # PyInstaller onedir: store Models next to the .exe, not inside _internal/
        return os.path.join(os.path.dirname(sys.executable), "Models")
    if IS_MAC:
        return os.path.join(os.path.expanduser("~"), "Library",
                            "Application Support", "WhisperX", "Models")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "Models")


def _available_devices():
    """Returns device list. Safe to call from any thread; imports torch lazily."""
    try:
        import torch
        devs = ["auto", "cpu"]
        if torch.cuda.is_available():
            devs.insert(1, "cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devs.insert(1, "mps")
        return devs
    except Exception:
        return ["auto", "cpu"]


# ── Reusable UI builders ──────────────────────────────────────────────────────
def card(parent, title=None):
    f = ctk.CTkFrame(parent, fg_color=_CARD, corner_radius=12)
    f.grid_columnconfigure(0, weight=1)
    if title:
        ctk.CTkLabel(f, text=title.upper(),
                     font=F(9, "bold"), text_color=_SECHI
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))
    return f


def section_title(parent, title, subtitle, row):
    ctk.CTkLabel(parent, text=title, font=F(20, "bold"),
                 text_color=_PRI).grid(row=row, column=0, sticky="w",
                                       pady=(0, 3))
    ctk.CTkLabel(parent, text=subtitle, font=F(12),
                 text_color=_HINT).grid(row=row + 1, column=0, sticky="w",
                                        pady=(0, 18))


def labeled_widget(parent, label, widget, row, hint=None):
    ctk.CTkLabel(parent, text=label, font=F(12),
                 text_color=_LABEL).grid(row=row, column=0, columnspan=2,
                                         sticky="w", padx=16,
                                         pady=(12 if row == 1 else 4, 2))
    widget.grid(row=row + 1, column=0, columnspan=2, sticky="ew",
                padx=16, pady=(0, 4 if hint else 0))
    if hint:
        ctk.CTkLabel(parent, text=hint, font=F(10),
                     text_color=_HINT).grid(row=row + 2, column=0,
                                             columnspan=2, sticky="w",
                                             padx=16, pady=(0, 4))


def browse_row(parent, label, var, cmd, row):
    ctk.CTkLabel(parent, text=label, font=F(12),
                 text_color=_LABEL).grid(row=row, column=0, columnspan=2,
                                         sticky="w", padx=16,
                                         pady=(12 if row == 0 else 4, 2))
    e = ctk.CTkEntry(parent, textvariable=var, font=F(12), height=36,
                     corner_radius=8, fg_color=_ENTRY,
                     border_color=_BORDER, border_width=1)
    e.grid(row=row + 1, column=0, sticky="ew", padx=(16, 6), pady=(0, 12))
    ctk.CTkButton(parent, text="...", width=42, height=36, corner_radius=8,
                  fg_color=_MID, hover_color=_MIDHOV,
                  font=F(14), command=cmd
                  ).grid(row=row + 1, column=1, padx=(0, 16), pady=(0, 12))


def combo(parent, var, values, width=None):
    kw = dict(variable=var, values=values, state="readonly", height=36,
              corner_radius=8, fg_color=_ENTRY, border_color=_BORDER,
              button_color=_MID, button_hover_color=_MIDHOV,
              dropdown_fg_color=_DROP, font=F(12))
    if width:
        kw["width"] = width
    return ctk.CTkComboBox(parent, **kw)


def entry(parent, var, width=None, placeholder=""):
    kw = dict(textvariable=var, font=F(12), height=36, corner_radius=8,
              fg_color=_ENTRY, border_color=_BORDER, border_width=1,
              placeholder_text=placeholder)
    if width:
        kw["width"] = width
    return ctk.CTkEntry(parent, **kw)


def toggle_row(parent, label, sub, var, row):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.grid(row=row, column=0, columnspan=2, sticky="ew",
           padx=16, pady=(8, 8))
    f.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(f, text=label, font=F(12),
                 text_color=_TOGG_L).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(f, text=sub, font=F(10),
                 text_color=_HINT).grid(row=1, column=0, sticky="w")
    ctk.CTkSwitch(f, text="", variable=var, width=44,
                  button_color="#4a9eff",
                  progress_color="#4a9eff").grid(row=0, column=1, rowspan=2,
                                                  padx=(12, 0))


# ── Main App ──────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WhisperX")
        self.geometry("920x660")
        self.minsize(820, 580)

        self._stop       = threading.Event()
        self._q          = queue.Queue()
        self._panels     = {}
        self._nav_key    = None
        self._device_combo = None  # populated by background probe

        self._build()
        self._setup_icon()
        self._poll_log()
        self._nav("Files")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        if IS_MAC:
            self.createcommand("tk::mac::Quit", self._on_close)

        # Probe for GPU devices in a background thread so torch import
        # does not block the window from appearing on first launch.
        threading.Thread(target=self._probe_devices, daemon=True).start()

    # ── Device probe (background) ─────────────────────────────────────────────

    def _probe_devices(self):
        devs = _available_devices()
        if self._device_combo is not None:
            self.after(0, lambda: self._device_combo.configure(values=devs))

    # ── Icon ──────────────────────────────────────────────────────────────────

    def _setup_icon(self):
        # Try a pre-built icon file first (present in packaged builds).
        ico_candidates = []
        if getattr(sys, "frozen", False):
            ico_candidates.append(
                os.path.join(os.path.dirname(sys.executable), "assets", "icon.ico"))
        ico_candidates += [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico"),
        ]

        for path in ico_candidates:
            if os.path.isfile(path) and IS_WIN:
                try:
                    self.after(50, lambda p=path: self.iconbitmap(p))
                    return
                except Exception:
                    pass

        # Fall back to generating the icon at runtime using PIL.
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageTk
            import tempfile

            size = 128
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([0, 0, size - 1, size - 1],
                                radius=size // 6,
                                fill=(74, 158, 255, 255))

            font = None
            for path in [
                "C:/Windows/Fonts/arialbd.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]:
                try:
                    font = ImageFont.truetype(path, int(size * 0.70))
                    break
                except Exception:
                    continue
            if font is None:
                font = ImageFont.load_default()

            bb = d.textbbox((0, 0), "W", font=font)
            x = (size - (bb[2] - bb[0])) // 2 - bb[0]
            y = (size - (bb[3] - bb[1])) // 2 - bb[1] - int(size * 0.04)
            d.text((x, y), "W", fill=(255, 255, 255, 255), font=font)

            if IS_WIN:
                ico_path = os.path.join(tempfile.gettempdir(), "whisperx.ico")
                img.save(ico_path, format="ICO",
                         sizes=[(128, 128), (64, 64), (32, 32), (16, 16)])
                self.after(50, lambda: self.iconbitmap(ico_path))

            self._icon_img = ImageTk.PhotoImage(
                img.resize((64, 64), Image.Resampling.LANCZOS))
            self.iconphoto(True, self._icon_img)

        except Exception:
            pass

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sb = ctk.CTkFrame(self, width=210, corner_radius=0,
                                fg_color=_SB)
        self._sb.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._sb.grid_propagate(False)
        self._sb.grid_rowconfigure(10, weight=1)
        self._build_sidebar()

        self._content_wrap = ctk.CTkFrame(self, corner_radius=0,
                                          fg_color=_CONT)
        self._content_wrap.grid(row=0, column=1, sticky="nsew")
        self._content_wrap.grid_rowconfigure(0, weight=1)
        self._content_wrap.grid_columnconfigure(0, weight=1)
        self._build_content()

        self._bar = ctk.CTkFrame(self, height=52, corner_radius=0,
                                 fg_color=_BAR)
        self._bar.grid(row=1, column=1, sticky="ew")
        self._build_statusbar()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = self._sb

        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 0))
        ctk.CTkLabel(logo, text="WhisperX", font=F(17, "bold"),
                     text_color=_PRI).pack(anchor="w")
        ctk.CTkLabel(logo, text="Transcriber", font=F(11),
                     text_color=_LOGO_S).pack(anchor="w")

        ctk.CTkFrame(sb, height=1, fg_color=_SEP).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(20, 12))

        self._nav_btns = {}
        for i, (key, label) in enumerate([
            ("Files",    "  Transcribe"),
            ("Model",    "  Quality"),
            ("Output",   "  Save"),
            ("Advanced", "  Settings"),
        ], start=2):
            btn = ctk.CTkButton(
                sb, text=label, anchor="w", font=F(13), height=40,
                corner_radius=9, fg_color="transparent",
                hover_color=_NAVHOV, text_color=_NAV_OF,
                command=lambda k=key: self._nav(k),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=10, pady=1)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sb, height=1, fg_color=_SEP).grid(
            row=7, column=0, sticky="ew", padx=16, pady=(14, 10))

        self._log_btn = ctk.CTkButton(
            sb, text="  Activity", anchor="w", font=F(13), height=40,
            corner_radius=9, fg_color="transparent",
            hover_color=_NAVHOV, text_color=_PRI,
            command=self._toggle_log,
        )
        self._log_btn.grid(row=8, column=0, sticky="ew", padx=10, pady=1)

        ctk.CTkButton(
            sb, text="  ♥  Support", anchor="w", font=F(12), height=36,
            corner_radius=9, fg_color="transparent",
            hover_color=_NAVHOV, text_color=("#c44569", "#e05c8a"),
            command=self._show_support,
        ).grid(row=9, column=0, sticky="ew", padx=10, pady=(1, 0))

        ctk.CTkFrame(sb, fg_color="transparent").grid(row=10, column=0,
                                                      sticky="nsew")

        ctk.CTkFrame(sb, height=1, fg_color=_SEP).grid(
            row=11, column=0, sticky="ew", padx=16, pady=(0, 12))
        tf = ctk.CTkFrame(sb, fg_color="transparent")
        tf.grid(row=12, column=0, sticky="ew", padx=16, pady=(0, 24))
        tf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tf, text="Dark mode", font=F(11),
                     text_color=_LOGO_S).grid(row=0, column=0, sticky="w")
        self._theme_sw = ctk.CTkSwitch(tf, text="", width=44,
                                       button_color="#4a9eff",
                                       progress_color="#4a9eff",
                                       command=self._toggle_theme)
        self._theme_sw.grid(row=0, column=1)
        self._theme_sw.select()

    # ── Content panels ────────────────────────────────────────────────────────

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self._content_wrap, fg_color="transparent",
            corner_radius=0, scrollbar_button_color=_SCRL_B,
            scrollbar_button_hover_color=_SCRL_H)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self._scroll = scroll

        self._panels["Files"]    = self._panel_files(scroll)
        self._panels["Model"]    = self._panel_model(scroll)
        self._panels["Output"]   = self._panel_output(scroll)
        self._panels["Advanced"] = self._panel_advanced(scroll)

        self._log_wrap = ctk.CTkFrame(self._content_wrap, fg_color=_BAR,
                                      corner_radius=0, height=220)
        self._log_wrap.grid(row=1, column=0, sticky="ew")
        self._log_wrap.grid_propagate(False)
        self._log_wrap.grid_columnconfigure(0, weight=1)
        self._log_wrap.grid_rowconfigure(2, weight=1)

        ctk.CTkFrame(self._log_wrap, height=1, fg_color=_SEP,
                     corner_radius=0).grid(row=0, column=0, sticky="ew")

        lh = ctk.CTkFrame(self._log_wrap, fg_color=_BAR,
                          corner_radius=0, height=28)
        lh.grid(row=1, column=0, sticky="ew")
        lh.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lh, text="  ACTIVITY", font=F(9, "bold"),
                     text_color=_LOG_H).grid(row=0, column=0, sticky="w",
                                              pady=5)
        ctk.CTkButton(lh, text="Clear", width=52, height=22, font=F(10),
                      fg_color="transparent", hover_color=_NAVACT,
                      text_color=_NAV_OF,
                      command=self._clear_log).grid(row=0, column=1,
                                                     padx=8, pady=3)

        self.log_area = ctk.CTkTextbox(
            self._log_wrap, font=FM(10), fg_color=_BAR,
            text_color=_LOG_B, corner_radius=0, state="disabled",
            scrollbar_button_color=_SCRL_B)
        self.log_area.grid(row=2, column=0, sticky="nsew")

        self._log_visible = True

    # ── Files panel ───────────────────────────────────────────────────────────

    def _panel_files(self, parent):
        p = ctk.CTkFrame(parent, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        section_title(p, "Transcribe",
                      "Select your media file and set the transcription language.", 0)

        c1 = card(p, "Media File")
        c1.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)
        self.v_file = ctk.StringVar()
        browse_row(c1, "Audio or Video File", self.v_file, self._browse_file, 0)

        c2 = card(p, "Language")
        c2.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)
        self._lang_map = {
            "Auto-detect":  "auto",
            "English":      "en",
            "Arabic":       "ar",
            "Chinese":      "zh",
            "Dutch":        "nl",
            "French":       "fr",
            "Georgian":     "ka",
            "German":       "de",
            "Hindi":        "hi",
            "Italian":      "it",
            "Japanese":     "ja",
            "Korean":       "ko",
            "Pashto":       "ps",
            "Persian":      "fa",
            "Polish":       "pl",
            "Portuguese":   "pt",
            "Russian":      "ru",
            "Spanish":      "es",
            "Turkish":      "tr",
            "Urdu":         "ur",
        }
        self.v_lang = ctk.StringVar(value="Auto-detect")
        ctk.CTkLabel(c2, text="Spoken language in the audio",
                     font=F(10), text_color=_HINT).grid(
            row=1, column=0, sticky="w", padx=16, pady=(10, 4))
        combo(c2, self.v_lang,
              list(self._lang_map.keys()),
              width=200).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))

        return p

    # ── Model panel ───────────────────────────────────────────────────────────

    def _panel_model(self, parent):
        p = ctk.CTkFrame(parent, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        section_title(p, "Quality",
                      "Adjust accuracy and speed to match your needs.", 0)

        c1 = card(p, "Model")
        c1.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self.v_model   = ctk.StringVar(value="large-v2")
        self.v_device  = ctk.StringVar(value="auto")
        self.v_compute = ctk.StringVar(value="int8" if IS_MAC else "float16")

        for i, (lbl, var, vals) in enumerate([
            ("Model", self.v_model,
             ["tiny", "tiny.en", "base", "base.en", "small", "small.en",
              "medium", "medium.en", "large-v1", "large-v2", "large-v3"]),
            ("Precision", self.v_compute,
             ["int8", "float16", "float32", "int8_float16"]),
        ]):
            r = 1 + i * 3
            ctk.CTkLabel(c1, text=lbl, font=F(12),
                         text_color=_LABEL).grid(row=r, column=0, sticky="w",
                                                  padx=16,
                                                  pady=(12 if i == 0 else 6, 2))
            combo(c1, var, vals).grid(row=r + 1, column=0, sticky="ew",
                                      padx=16, pady=(0, 4))

        # Device combo starts with safe defaults; _probe_devices() fills real list.
        ctk.CTkLabel(c1, text="Device", font=F(12),
                     text_color=_LABEL).grid(row=7, column=0, sticky="w",
                                              padx=16, pady=(6, 2))
        self._device_combo = combo(c1, self.v_device, ["auto", "cpu"])
        self._device_combo.grid(row=8, column=0, sticky="ew",
                                padx=16, pady=(0, 4))

        ctk.CTkFrame(c1, height=12, fg_color="transparent").grid(
            row=99, column=0)

        c2 = card(p, "Expert Tuning")
        c2.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)
        c2.grid_columnconfigure(1, weight=1)
        c2.grid_columnconfigure(2, weight=1)

        self.v_batch = ctk.StringVar(value="8" if IS_MAC else "16")
        self.v_beam  = ctk.StringVar(value="5")
        self.v_chunk = ctk.StringVar(value="30")

        for col, (lbl, var, hint) in enumerate([
            ("Speed",        self.v_batch, "Higher = faster, needs more VRAM"),
            ("Accuracy",     self.v_beam,  "Higher = more accurate, slower"),
            ("Segment (s)",  self.v_chunk, "Audio chunk size in seconds"),
        ]):
            ctk.CTkLabel(c2, text=lbl, font=F(11),
                         text_color=_LABEL).grid(
                row=1, column=col, sticky="w", padx=14, pady=(14, 2))
            entry(c2, var, width=90).grid(
                row=2, column=col, sticky="ew", padx=14, pady=(0, 4))
            ctk.CTkLabel(c2, text=hint, font=F(10),
                         text_color=_HINT).grid(
                row=3, column=col, sticky="w", padx=14, pady=(0, 14))

        if IS_MAC:
            note = ctk.CTkFrame(p, fg_color=_MAC_BG, corner_radius=10)
            note.grid(row=4, column=0, sticky="ew", pady=(0, 10))
            note.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(note,
                         text="  Mac: Transcription on CPU  |  Alignment on MPS (Apple Silicon)",
                         font=F(11), text_color=_MAC_TXT).grid(
                padx=14, pady=12, sticky="w")

        return p

    # ── Output panel ──────────────────────────────────────────────────────────

    def _panel_output(self, parent):
        p = ctk.CTkFrame(parent, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        section_title(p, "Save",
                      "Choose where to save your files and which formats to export.", 0)

        c1 = card(p, "Save Location")
        c1.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)
        self.v_out_dir = ctk.StringVar()
        browse_row(c1, "Save to Folder", self.v_out_dir,
                   self._browse_out_dir, 0)

        c2 = card(p, "Export Formats")
        c2.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)
        c2.grid_columnconfigure(1, weight=1)

        self.v_fmts = {}
        fmts = [
            ("word_json", "Word-level JSON", "Per-word timestamps & scores", True),
            ("srt",       "SRT",             "Standard subtitles",           False),
            ("vtt",       "VTT",             "WebVTT subtitles",             False),
            ("txt",       "TXT",             "Plain text transcript",        False),
            ("tsv",       "TSV",             "Tab-separated data",           False),
            ("json",      "JSON",            "Segment-level data",           False),
        ]
        for i, (key, name, desc, default) in enumerate(fmts):
            v = ctk.BooleanVar(value=default)
            self.v_fmts[key] = v
            r, c = divmod(i, 2)
            f = ctk.CTkFrame(c2, fg_color=_FMT, corner_radius=8)
            f.grid(row=r + 1, column=c, sticky="ew",
                   padx=(14 if c == 0 else 6, 6 if c == 0 else 14),
                   pady=4)
            f.grid_columnconfigure(1, weight=1)
            ctk.CTkCheckBox(f, text="", variable=v, width=20,
                            checkbox_width=18, checkbox_height=18,
                            checkmark_color="#ffffff",
                            fg_color="#4a9eff",
                            hover_color="#3a7acc").grid(
                row=0, column=0, padx=(12, 8), pady=12)
            ctk.CTkLabel(f, text=name, font=F(12, "bold"),
                         text_color=_FMT_N).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(f, text=desc, font=F(10),
                         text_color=_FMT_D).grid(row=0, column=2,
                                                   sticky="e", padx=(0, 12))

        ctk.CTkFrame(c2, height=8, fg_color="transparent").grid(
            row=99, column=0, columnspan=2)

        c3 = card(p, "Word Timestamps")
        c3.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)
        self.v_align = ctk.BooleanVar(value=True)
        toggle_row(c3, "Word timestamps",
                   "Adds per-word timing — required for Word-level JSON and karaoke highlighting",
                   self.v_align, 1)

        c4 = card(p, "Silence Removal")
        c4.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        c4.grid_columnconfigure(0, weight=1)
        self.v_vad = ctk.BooleanVar(value=True)
        toggle_row(c4, "Remove silence",
                   "Skips quiet sections before transcribing — faster and cleaner results",
                   self.v_vad, 1)

        return p

    # ── Advanced panel ────────────────────────────────────────────────────────

    def _panel_advanced(self, parent):
        p = ctk.CTkFrame(parent, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        section_title(p, "Settings",
                      "Fine-tune silence detection, subtitle formatting, and AI model storage.", 0)

        c1 = card(p, "Silence Detection")
        c1.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        c1.grid_columnconfigure(0, weight=1)

        self.v_vad_onset  = ctk.StringVar(value="0.500")
        self.v_vad_offset = ctk.StringVar(value="0.363")

        ctk.CTkLabel(c1, text="Adjust how aggressively silence is detected.",
                     font=F(10), text_color=_HINT).grid(
            row=1, column=0, sticky="w", padx=16, pady=(10, 6))
        vf = ctk.CTkFrame(c1, fg_color="transparent")
        vf.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))
        for i, (lbl, var) in enumerate([("Sensitivity", self.v_vad_onset),
                                        ("Release",     self.v_vad_offset)]):
            ctk.CTkLabel(vf, text=lbl, font=F(11),
                         text_color=_LABEL).grid(row=0, column=i * 2,
                                                  sticky="w",
                                                  padx=(0 if i == 0 else 20, 8))
            entry(vf, var, width=88).grid(row=0, column=i * 2 + 1, sticky="w")

        c2 = card(p, "Subtitle Formatting")
        c2.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        c2.grid_columnconfigure(0, weight=1)

        self.v_highlight = ctk.BooleanVar(value=False)
        self.v_max_width = ctk.StringVar(value="")
        self.v_max_count = ctk.StringVar(value="")

        toggle_row(c2, "Karaoke highlighting",
                   "Word-by-word highlight effect for SRT and VTT subtitles",
                   self.v_highlight, 1)

        sf = ctk.CTkFrame(c2, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))
        for i, (lbl, var, ph) in enumerate([
            ("Max line width", self.v_max_width, "default"),
            ("Max line count", self.v_max_count, "default"),
        ]):
            ctk.CTkLabel(sf, text=lbl, font=F(11),
                         text_color=_LABEL).grid(row=0, column=i * 2,
                                                  sticky="w",
                                                  padx=(0 if i == 0 else 20, 8))
            entry(sf, var, width=88, placeholder=ph).grid(
                row=0, column=i * 2 + 1, sticky="w")

        c3 = card(p, "AI Models")
        c3.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        c3.grid_columnconfigure(0, weight=1)
        self.v_model_dir = ctk.StringVar(value=_default_model_dir())
        browse_row(c3, "AI Models Folder", self.v_model_dir,
                   self._browse_model_dir, 0)
        ctk.CTkLabel(c3, text="Where downloaded AI models are stored",
                     font=F(10), text_color=_HINT).grid(
            row=2, column=0, columnspan=2, sticky="w",
            padx=16, pady=(0, 12))

        return p

    # ── Support dialog ────────────────────────────────────────────────────────

    def _show_support(self):
        w = ctk.CTkToplevel(self)
        w.title("Support the Project")
        w.geometry("420x470")
        w.resizable(False, False)
        w.grab_set()
        w.focus_set()
        w.grid_columnconfigure(0, weight=1)
        w.grid_rowconfigure(0, weight=1)

        root = ctk.CTkFrame(w, fg_color=_CONT, corner_radius=0)
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(root, text="♥", font=F(30),
                     text_color=("#c44569", "#e05c8a")).grid(
            row=0, column=0, pady=(30, 2))
        ctk.CTkLabel(root, text="Support this project", font=F(18, "bold"),
                     text_color=_PRI).grid(row=1, column=0, pady=(0, 20))

        msg = ctk.CTkFrame(root, fg_color=_CARD, corner_radius=12)
        msg.grid(row=2, column=0, padx=28, sticky="ew", pady=(0, 22))
        msg.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            msg,
            text=(
                "I'm a working student engineer and part-time researcher\n"
                "building this entirely in my spare time — free, forever.\n\n"
                "If this app has saved you hours of work, a small contribution\n"
                "goes a long way and keeps development moving forward."
            ),
            font=F(12), text_color=_LABEL,
            justify="center", wraplength=340,
        ).grid(row=0, column=0, padx=20, pady=16)

        def _open(url):
            return lambda: webbrowser.open(url)

        ctk.CTkButton(
            root, text="♥   Sponsor on GitHub", height=42, corner_radius=10,
            fg_color=("#c44569", "#d63384"), hover_color=("#a83058", "#bf2070"),
            text_color="#ffffff", font=F(13, "bold"),
            command=_open("https://github.com/sponsors/ibrahimqureshae"),
        ).grid(row=3, column=0, padx=28, sticky="ew", pady=(0, 10))

        ctk.CTkButton(
            root, text="   Donate via PayPal", height=42, corner_radius=10,
            fg_color=("#0070ba", "#0085cc"), hover_color=("#005ea0", "#006eb0"),
            text_color="#ffffff", font=F(13, "bold"),
            command=_open("https://www.paypal.me/mibrahimqr"),
        ).grid(row=4, column=0, padx=28, sticky="ew", pady=(0, 10))

        ctk.CTkButton(
            root, text="★   Star on GitHub  —  it's free!", height=38,
            corner_radius=10, fg_color="transparent", hover_color=_NAVHOV,
            text_color=_LOGO_S, border_width=1, border_color=_BORDER,
            font=F(12),
            command=_open("https://github.com/ibrahimqureshae/whisperx-transcriber"),
        ).grid(row=5, column=0, padx=28, sticky="ew", pady=(0, 28))

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = self._bar
        bar.grid_columnconfigure(2, weight=1)

        self._dot = ctk.CTkLabel(bar, text="●", font=F(10),
                                 text_color="#34c759", width=16)
        self._dot.grid(row=0, column=0, padx=(18, 4))

        self._status_var = ctk.StringVar(value="Ready")
        ctk.CTkLabel(bar, textvariable=self._status_var,
                     font=F(12), text_color=_STAT).grid(row=0, column=1,
                                                          sticky="w")

        self._progress = ctk.CTkProgressBar(bar, width=180, height=3,
                                            corner_radius=2,
                                            mode="indeterminate",
                                            fg_color=_PROG_BG,
                                            progress_color="#4a9eff")
        self._progress.grid(row=0, column=2, padx=20)
        self._progress.set(0)

        self._stop_btn = ctk.CTkButton(
            bar, text="Cancel", width=72, height=34, corner_radius=8,
            fg_color="transparent", hover_color=_BAR,
            text_color=_BAR, text_color_disabled=_BAR,
            border_width=0, state="disabled",
            font=F(12), command=self._on_stop)
        self._stop_btn.grid(row=0, column=3, padx=(0, 8))

        self._run_btn = ctk.CTkButton(
            bar, text="Transcribe", width=100, height=34, corner_radius=8,
            fg_color="#4a9eff", hover_color="#6ab0ff",
            text_color="#ffffff",
            font=F(13, "bold"), command=self._on_run)
        self._run_btn.grid(row=0, column=4, padx=(0, 18))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _nav(self, key):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color=_NAVACT, text_color=_PRI)
            else:
                btn.configure(fg_color="transparent", text_color=_NAV_OF)
        self._nav_key = key
        for k, panel in self._panels.items():
            if k == key:
                panel.grid(row=0, column=0, sticky="nsew", padx=28, pady=24)
            else:
                panel.grid_remove()

    # ── Log toggle ────────────────────────────────────────────────────────────

    def _toggle_log(self):
        if self._log_visible:
            self._log_wrap.grid_remove()
            self._log_btn.configure(text_color=_NAV_OF)
        else:
            self._log_wrap.grid(row=1, column=0, sticky="ew")
            self._log_btn.configure(text_color=_PRI)
        self._log_visible = not self._log_visible

    def _toggle_theme(self):
        ctk.set_appearance_mode(
            "dark" if self._theme_sw.get() else "light")

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log(self, msg):
        self._q.put(str(msg))
        if not self._log_visible:
            self.after(0, self._toggle_log)

    def _clear_log(self):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    def _poll_log(self):
        while True:
            try:
                msg = self._q.get_nowait()
                self.log_area.configure(state="normal")
                self.log_area.insert("end", msg + "\n")
                self.log_area.see("end")
                self.log_area.configure(state="disabled")
            except queue.Empty:
                break
        self.after(100, self._poll_log)

    # ── Browse helpers ────────────────────────────────────────────────────────

    def _browse_file(self):
        p = filedialog.askopenfilename(
            title="Select Audio / Video",
            filetypes=[("Media",
                        "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav "
                        "*.m4a *.flac *.ogg *.webm"),
                       ("All", "*.*")])
        if p:
            self.v_file.set(p)
            if not self.v_out_dir.get():
                self.v_out_dir.set(os.path.dirname(p))

    def _browse_model_dir(self):
        p = filedialog.askdirectory(title="AI Models Folder")
        if p:
            self.v_model_dir.set(p)

    def _browse_out_dir(self):
        p = filedialog.askdirectory(title="Save to Folder")
        if p:
            self.v_out_dir.set(p)

    # ── Run / Stop ────────────────────────────────────────────────────────────

    def _on_run(self):
        if not self.v_file.get().strip():
            messagebox.showerror("Missing input",
                                 "Please select an audio/video file.")
            return
        if not self.v_out_dir.get().strip():
            messagebox.showerror("Missing output",
                                 "Please select an output directory.")
            return
        if not any(v.get() for v in self.v_fmts.values()):
            messagebox.showerror("No format",
                                 "Select at least one output format.")
            return

        def safe_int(s, default):
            try: return int(s)
            except Exception: return default

        def safe_float(s, default):
            try: return float(s)
            except Exception: return default

        cfg = {
            "audio":      self.v_file.get().strip(),
            "model_dir":  self.v_model_dir.get().strip(),
            "model":      self.v_model.get(),
            "device":     self.v_device.get(),
            "compute":    self.v_compute.get(),
            "batch":      safe_int(self.v_batch.get(), 16),
            "beam":       safe_int(self.v_beam.get(), 5),
            "chunk":      safe_int(self.v_chunk.get(), 30),
            "out_dir":    self.v_out_dir.get().strip(),
            "formats":    [k for k, v in self.v_fmts.items() if v.get()],
            "align":      bool(self.v_align.get()),
            "language":   self._lang_map.get(self.v_lang.get(), "auto"),
            "vad":        bool(self.v_vad.get()),
            "vad_onset":  safe_float(self.v_vad_onset.get(), 0.5),
            "vad_offset": safe_float(self.v_vad_offset.get(), 0.363),
            "highlight":  bool(self.v_highlight.get()),
            "max_width":  safe_int(self.v_max_width.get(), None)
                          if self.v_max_width.get().strip().isdigit() else None,
            "max_count":  safe_int(self.v_max_count.get(), None)
                          if self.v_max_count.get().strip().isdigit() else None,
        }

        self._stop.clear()
        self._run_btn.configure(state="disabled", fg_color="#2a5a8a")
        self._stop_btn.configure(state="normal", text_color=("#cc3333", "#ff453a"),
                                  hover_color=_NAVHOV)
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        self._status_var.set("Running...")
        self._dot.configure(text_color="#ff9f0a")
        threading.Thread(target=self._worker, args=(cfg,), daemon=True).start()

    def _on_close(self):
        self._stop.set()
        try:
            self.destroy()
        finally:
            os._exit(0)

    def _on_stop(self):
        self._stop.set()
        self._log("Stopping after current operation...")
        self._status_var.set("Stopping...")
        self._stop_btn.configure(state="disabled", text_color=_BAR,
                                  hover_color=_BAR)

    def _worker(self, cfg):
        try:
            from core import pipeline
            os.environ["HF_HOME"] = cfg["model_dir"]

            # ── Device ───────────────────────────────────────────────────────
            _, t_dev, a_dev = pipeline.detect_device(cfg["device"])
            compute, adjusted = pipeline.resolve_compute(t_dev, cfg["compute"])
            if adjusted:
                self._log("  float16 not supported on CPU — using int8")
            self._log(f"Device: {t_dev.upper()}   Compute: {compute}")
            if a_dev != t_dev:
                self._log(f"Alignment: {a_dev.upper()}")
            if self._stop.is_set():
                return

            lang = None if cfg["language"] == "auto" else cfg["language"]

            # ── Model ─────────────────────────────────────────────────────────
            model_cache = os.path.join(
                cfg["model_dir"], "hub",
                f"models--Systran--faster-whisper-{cfg['model']}")
            if not os.path.isdir(model_cache):
                self._log(f"Downloading model '{cfg['model']}' for the first time...")
                self._log("  This may take several minutes depending on your connection.")
                self._log("  The model will be saved and reused on all future runs.")
                self.after(0, lambda: self._status_var.set("Downloading model..."))
            else:
                self._log(f"Loading model '{cfg['model']}' from cache...")
                self.after(0, lambda: self._status_var.set("Loading model..."))

            model = pipeline.load_model(
                cfg["model"], t_dev, compute, lang, cfg["beam"])
            if self._stop.is_set():
                return

            # ── Audio ─────────────────────────────────────────────────────────
            self._log("Loading audio...")
            self.after(0, lambda: self._status_var.set("Loading audio..."))
            audio = pipeline.load_audio(cfg["audio"])
            if self._stop.is_set():
                return

            # ── Transcribe ────────────────────────────────────────────────────
            self._log("Transcribing...")
            self.after(0, lambda: self._status_var.set("Transcribing..."))
            result, det = pipeline.transcribe(model, audio, cfg["batch"], lang)
            self._log(f"  Language: {det}   Segments: {len(result['segments'])}")
            if self._stop.is_set():
                return

            # ── Align ─────────────────────────────────────────────────────────
            needs_align = cfg["align"] and (
                "word_json" in cfg["formats"] or cfg["highlight"])
            if needs_align:
                self._log("Aligning word timestamps...")
                self.after(0, lambda: self._status_var.set("Aligning..."))
                try:
                    result = pipeline.align(result, det, a_dev, audio)
                except Exception as e:
                    self._log(f"  Alignment failed: {e} — continuing without word timestamps")
                    result.setdefault("language", det)
            else:
                result.setdefault("language", det)
            if self._stop.is_set():
                return

            # ── Export ────────────────────────────────────────────────────────
            self._log("Saving files...")
            self.after(0, lambda: self._status_var.set("Saving..."))
            last_path = None
            for fmt, path, err in pipeline.export(
                    result, cfg["formats"], cfg["out_dir"], cfg["audio"],
                    {"max_width": cfg["max_width"],
                     "max_count": cfg["max_count"],
                     "highlight": cfg["highlight"]}):
                if err:
                    self._log(f"  {fmt} error: {err}")
                else:
                    self._log(f"  {fmt:<10}->  {path}")
                    last_path = path

            self._log("Done!")
            self.after(0, lambda: self._status_var.set("Done"))
            self.after(0, lambda: self._dot.configure(text_color="#34c759"))
            if last_path:
                folder = os.path.dirname(os.path.abspath(last_path))
                self.after(0, lambda f=folder: subprocess.Popen(
                    ["explorer", f], creationflags=subprocess.CREATE_NO_WINDOW))

        except Exception as e:
            self._log(f"ERROR: {e}\n{traceback.format_exc()}")
            self.after(0, lambda: self._status_var.set("Error"))
            self.after(0, lambda: self._dot.configure(text_color="#ff3b30"))
        finally:
            if self._stop.is_set():
                self.after(0, lambda: self._status_var.set("Stopped"))
                self.after(0, lambda: self._dot.configure(text_color="#888888"))
            self.after(0, self._reset_btns)

    def _reset_btns(self):
        self._run_btn.configure(state="normal", fg_color="#4a9eff")
        self._stop_btn.configure(state="disabled", text_color=_BAR,
                                  hover_color=_BAR)
        self._progress.stop()
        self._progress.set(0)


if __name__ == "__main__":
    App().mainloop()

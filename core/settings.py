"""Project-local HF token storage shared by the GUI and CLI."""
import json
import os
from pathlib import Path
import re
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = PROJECT_ROOT / "settings.json"


class SettingsError(RuntimeError):
    """The project settings could not be read or saved."""


def load_hf_token() -> str | None:
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise SettingsError("Could not read project settings.json.") from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise SettingsError("Invalid project settings.json format.")
    token = data.get("hf_token", "")
    if not isinstance(token, str):
        raise SettingsError("Invalid HF token in project settings.json.")
    return token.strip() or None


def save_hf_token(token: str) -> None:
    token = token.strip()
    if not token:
        delete_hf_token()
        return
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=SETTINGS_PATH.parent,
                prefix=".settings-", suffix=".tmp", delete=False) as fh:
            temp_path = Path(fh.name)
            if os.name == "posix":
                os.chmod(temp_path, 0o600)
            json.dump({"version": 1, "hf_token": token}, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, SETTINGS_PATH)
    except OSError as exc:
        raise SettingsError(
            "Could not save HF token in project settings.json. "
            "Check that the project folder is writable.") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError as exc:
                raise SettingsError(
                    "Could not remove the temporary project settings file.") from exc


def delete_hf_token() -> None:
    try:
        SETTINGS_PATH.unlink(missing_ok=True)
    except OSError as exc:
        raise SettingsError("Could not remove project settings.json.") from exc


def resolve_hf_token(explicit_token: str | None = None) -> str | None:
    if explicit_token and explicit_token.strip():
        return explicit_token.strip()
    return load_hf_token() or os.environ.get("HF_TOKEN", "").strip() or None


def redact_secrets(message, *tokens) -> str:
    """Remove known tokens and HF-shaped secrets from user-visible diagnostics."""
    text = str(message)
    for token in tokens:
        if isinstance(token, str) and token.strip():
            text = text.replace(token.strip(), "[REDACTED]")
    return re.sub(r"\bhf_[A-Za-z0-9]{10,}\b", "[REDACTED]", text)

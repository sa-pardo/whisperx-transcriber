"""Repair regression tests without a GUI, downloads or installed ML packages."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from core.runtime import EXIT_NEEDS_SETUP, SETUP_VERSION


@pytest.fixture
def setup_module(monkeypatch):
    # Load the real installer, stubbing only the GUI dependency at import time.
    gui = SimpleNamespace(set_appearance_mode=lambda *_: None,
                          set_default_color_theme=lambda *_: None)
    monkeypatch.setitem(sys.modules, "customtkinter", gui)
    path = Path(__file__).resolve().parents[1] / "setup_wizard.py"
    spec = importlib.util.spec_from_file_location("_setup_wizard_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.subprocess, "CREATE_NO_WINDOW", 0, raising=False)
    monkeypatch.setattr(module, "_cuda_torch_index", lambda: None)
    monkeypatch.setattr(module, "_has_nvidia", lambda: False)
    return module


@pytest.fixture
def installation(setup_module, monkeypatch, tmp_path):
    runtime = tmp_path / "runtime"
    python = runtime / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.touch()
    marker = runtime / ".setup_complete"
    marker.write_text(SETUP_VERSION)
    corrupt = runtime / "corrupt-package.py"
    corrupt.write_text("broken package with valid metadata")
    model = tmp_path / "Models" / "cached-model.bin"
    model.parent.mkdir()
    model.write_bytes(b"keep model")
    settings = tmp_path / "settings.json"
    settings.write_text('{"keep": true}')

    wizard = setup_module.SetupWizard.__new__(setup_module.SetupWizard)
    wizard.base_dir = str(tmp_path)
    wizard.runtime_dir = str(runtime)
    wizard.python_path = "system-python"
    wizard.repair = False
    logs, statuses, commands, pip_commands = [], [], [], []
    wizard.win = SimpleNamespace(after=lambda *args: None)
    wizard._log = logs.append
    wizard._set_status = statuses.append
    wizard._set_progress = lambda *args: None
    state = SimpleNamespace(final_code=0, final_error="", final_timeout=False, pip_code=0)

    def run(command, **kwargs):
        commands.append(command)
        if command[1:3] == ["-m", "venv"]:
            python.parent.mkdir(parents=True, exist_ok=True)
            python.touch()
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if "-c" in command:
            return subprocess.CompletedProcess(command, 0, stdout="13\n", stderr="")
        assert command[1].endswith("runtime.py")
        assert "--quick" not in command
        assert kwargs["timeout"] == 120
        assert not marker.exists(), "Success marker must be invalidated before validation"
        if "--torch-only" in command:
            code = 0 if corrupt.exists() else EXIT_NEEDS_SETUP
            return subprocess.CompletedProcess(command, code, stdout="", stderr="")
        if state.final_timeout:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return subprocess.CompletedProcess(command, state.final_code,
                                           stdout="", stderr=state.final_error)

    def run_pip(command):
        assert not marker.exists()
        pip_commands.append(command)
        return state.pip_code

    monkeypatch.setattr(setup_module.subprocess, "run", run)
    wizard._run_pip = run_pip
    return SimpleNamespace(wizard=wizard, runtime=runtime, marker=marker, corrupt=corrupt,
                           model=model, settings=settings, commands=commands,
                           pip_commands=pip_commands, logs=logs, statuses=statuses, state=state)


@pytest.mark.parametrize("gpu", [False, True])
def test_repair_rebuilds_all_packages_and_preserves_user_data(
        setup_module, installation, monkeypatch, gpu):
    i = installation
    i.wizard.repair = True
    monkeypatch.setattr(setup_module, "_cuda_torch_index",
                        lambda: "https://download.pytorch.org/whl/cu128" if gpu else None)
    monkeypatch.setattr(setup_module, "_has_nvidia", lambda: gpu)
    i.wizard._run_install()

    assert not i.corrupt.exists()
    assert i.model.read_bytes() == b"keep model"
    assert i.settings.read_text() == '{"keep": true}'
    assert any(cmd[1:3] == ["-m", "venv"] for cmd in i.commands)
    requirement = "requirements-gpu.txt" if gpu else "requirements-cpu.txt"
    assert any(cmd[-1].endswith(requirement) for cmd in i.pip_commands)
    assert any(cmd[-1].endswith("requirements-core.txt") for cmd in i.pip_commands)
    probes = [cmd for cmd in i.commands if cmd[1].endswith("runtime.py")]
    assert all(("--cuda" in cmd) is gpu for cmd in probes)
    assert i.marker.read_text() == SETUP_VERSION
    assert i.statuses[-1] == "Setup complete!"


def test_normal_setup_reuses_existing_environment(installation):
    i = installation
    i.wizard._run_install()
    assert i.corrupt.exists()
    assert not any(cmd[1:3] == ["-m", "venv"] for cmd in i.commands)
    assert not any(cmd[-1].endswith("requirements-cpu.txt") for cmd in i.pip_commands)
    assert i.marker.read_text() == SETUP_VERSION


@pytest.mark.parametrize("repair", [False, True])
@pytest.mark.parametrize("returncode", [EXIT_NEEDS_SETUP, 1])
def test_failed_import_or_probe_never_leaves_success_marker(installation, repair, returncode):
    i = installation
    i.wizard.repair = repair
    i.state.final_code = returncode
    i.state.final_error = "ImportError: damaged backend"
    i.wizard._run_install()

    assert not i.marker.exists()
    assert "Setup failed" in i.statuses[-1]
    assert any("ImportError: damaged backend" in line for line in i.logs)
    assert i.model.read_bytes() == b"keep model"


def test_full_probe_timeout_does_not_mark_complete(installation):
    i = installation
    i.wizard.repair = True
    i.state.final_timeout = True
    i.wizard._run_install()
    assert not i.marker.exists()
    assert "Setup failed" in i.statuses[-1]


def test_failed_download_does_not_mark_complete(installation):
    i = installation
    i.wizard.repair = True
    i.state.pip_code = 1
    i.wizard._run_install()
    assert not i.marker.exists()
    assert "Setup failed" in i.statuses[-1]


def test_repair_stops_after_failed_runtime_removal(setup_module, installation, monkeypatch):
    i = installation
    i.wizard.repair = True

    def blocked(path):
        assert path == str(i.runtime)
        raise PermissionError("runtime is in use")

    monkeypatch.setattr(setup_module.shutil, "rmtree", blocked)
    i.wizard._run_install()
    assert i.pip_commands == []
    assert not i.marker.exists()
    assert i.corrupt.exists()
    assert any("runtime is in use" in line for line in i.logs)
    assert i.settings.read_text() == '{"keep": true}'


def test_full_probe_clears_frozen_tk_environment(setup_module, monkeypatch):
    wizard = setup_module.SetupWizard.__new__(setup_module.SetupWizard)
    wizard._log = lambda message: None
    monkeypatch.setattr(setup_module.sys, "frozen", True, raising=False)
    monkeypatch.setenv("TCL_LIBRARY", "bundled-tcl")
    monkeypatch.setenv("TK_LIBRARY", "bundled-tk")

    def run(command, **kwargs):
        assert "TCL_LIBRARY" not in kwargs["env"]
        assert "TK_LIBRARY" not in kwargs["env"]
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(setup_module.subprocess, "run", run)
    assert wizard._probe_runtime(["python", "runtime.py"])
    assert setup_module.os.environ["TCL_LIBRARY"] == "bundled-tcl"


def test_constructor_keeps_repair_explicit_until_user_starts(setup_module, monkeypatch, tmp_path):
    class Window:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    monkeypatch.setattr(setup_module.ctk, "CTk", Window, raising=False)
    monkeypatch.setattr(setup_module, "_find_python", lambda: "python")
    monkeypatch.setattr(setup_module.SetupWizard, "_build_shell", lambda self: None)
    monkeypatch.setattr(setup_module.SetupWizard, "_show_welcome", lambda self: None)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    sentinel = runtime / "keep-until-confirmed"
    sentinel.touch()
    wizard = setup_module.SetupWizard(str(tmp_path), lambda: None, repair=True)
    assert wizard.repair is True
    assert sentinel.exists()


def test_optional_decoder_warning_is_visible_without_failing_probe(
        setup_module, monkeypatch):
    wizard = setup_module.SetupWizard.__new__(setup_module.SetupWizard)
    messages = []
    wizard._log = messages.append

    def run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, stdout="",
            stderr="WARNING: TorchCodec native audio decoding is unavailable. "
                   "Continuing installation.",
        )

    monkeypatch.setattr(setup_module.subprocess, "run", run)

    assert wizard._probe_runtime(["python", "runtime.py"]) is True
    assert len(messages) == 1
    assert "TorchCodec native audio decoding is unavailable" in messages[0]

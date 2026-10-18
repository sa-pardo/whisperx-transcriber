"""Regression tests for the thin PyInstaller launcher's child process environment."""

import os
import subprocess
import pytest

import launcher


@pytest.mark.parametrize("frozen", [True, False])
def test_launch_app_uses_runtime_tcl_tk_paths(monkeypatch, tmp_path, frozen):
    """An external Python must not inherit PyInstaller's incompatible Tcl/Tk data."""
    app_script = tmp_path / "app.py"
    app_script.write_text("# stub app\n", encoding="utf-8")
    bootstrap_script = tmp_path / "app_bootstrap.py"
    bootstrap_script.write_text("# stub bootstrap\n", encoding="utf-8")
    runtime_py = tmp_path / "runtime" / "Scripts" / "pythonw.exe"
    runtime_py.parent.mkdir(parents=True)
    runtime_py.touch()

    monkeypatch.setattr(launcher, "_base_dir", lambda: str(tmp_path))
    monkeypatch.setattr(launcher, "_runtime_python", lambda: str(runtime_py))
    monkeypatch.setattr(launcher.sys, "frozen", frozen, raising=False)
    monkeypatch.setenv("TCL_LIBRARY", r"C:\bundle\_internal\_tcl_data")
    monkeypatch.setenv("TK_LIBRARY", r"C:\bundle\_internal\_tk_data")
    monkeypatch.setenv("WHISPERX_TEST_VAR", "preserved")

    launched = {}

    def fake_popen(args, **kwargs):
        launched["args"] = args
        launched["env"] = kwargs["env"]

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)

    with pytest.raises(SystemExit) as result:
        launcher._launch_app()

    assert result.value.code == 0
    assert launched["args"] == [str(runtime_py), str(bootstrap_script)]
    assert launched["env"]["PYTHONUTF8"] == "1"
    assert launched["env"]["WHISPERX_TEST_VAR"] == "preserved"

    if frozen:
        assert "TCL_LIBRARY" not in launched["env"]
        assert "TK_LIBRARY" not in launched["env"]
    else:
        # Plain source launches preserve explicitly configured user paths.
        assert launched["env"]["TCL_LIBRARY"] == os.environ["TCL_LIBRARY"]
        assert launched["env"]["TK_LIBRARY"] == os.environ["TK_LIBRARY"]

    # The parent process environment must never be modified.
    assert os.environ["TCL_LIBRARY"] == r"C:\bundle\_internal\_tcl_data"
    assert os.environ["TK_LIBRARY"] == r"C:\bundle\_internal\_tk_data"


def _create_installed_runtime(monkeypatch, tmp_path):
    python = tmp_path / "runtime" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.touch()
    marker = tmp_path / "runtime" / ".setup_complete"
    marker.write_text(launcher.SETUP_VERSION, encoding="utf-8")
    probe = tmp_path / "core" / "runtime.py"
    probe.parent.mkdir()
    probe.touch()
    (tmp_path / "runtime" / "Lib" / "site-packages" / "imageio_ffmpeg"
     / "binaries").mkdir(parents=True)
    monkeypatch.setattr(launcher, "_base_dir", lambda: str(tmp_path))
    return python, probe, marker


def test_valid_installation_uses_quick_metadata_probe(monkeypatch, tmp_path):
    python, probe, _ = _create_installed_runtime(monkeypatch, tmp_path)
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        assert kwargs["timeout"] == 12
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)
    monkeypatch.setattr(
        launcher, "cuda_torch_index",
        lambda: pytest.fail("Startup must never invoke nvidia-smi"),
        raising=False,
    )

    status, reason = launcher._runtime_status()

    assert status is launcher.RuntimeStatus.READY
    assert reason == ""
    assert calls == [[str(python), str(probe), "--quick"]]


def test_missing_dependencies_require_setup(monkeypatch, tmp_path):
    _create_installed_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, launcher.EXIT_NEEDS_SETUP),
    )

    status, reason = launcher._runtime_status()

    assert status is launcher.RuntimeStatus.NEEDS_SETUP
    assert "dependencies" in reason.lower() or "dependency" in reason.lower()


def test_probe_timeout_launches_instead_of_reinstalling(monkeypatch, tmp_path):
    _create_installed_runtime(monkeypatch, tmp_path)

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=kwargs["timeout"])

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    launches = []
    warnings = []
    monkeypatch.setattr(launcher, "_launch_app", lambda: launches.append(True))
    monkeypatch.setattr(launcher, "_log_startup_warning", warnings.append)

    launcher.main()

    assert launches == [True]
    assert len(warnings) == 1
    assert "unavailable" in warnings[0].lower()


@pytest.mark.parametrize("marker_contents", ["old-version", ""])
def test_outdated_or_empty_marker_requires_setup(monkeypatch, tmp_path, marker_contents):
    _, _, marker = _create_installed_runtime(monkeypatch, tmp_path)
    marker.write_text(marker_contents, encoding="utf-8")
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda *args, **kwargs: pytest.fail("Probe should not run without valid marker"),
    )

    status, reason = launcher._runtime_status()

    assert status is launcher.RuntimeStatus.NEEDS_SETUP
    assert "update" in reason.lower()


def test_missing_ffmpeg_requires_setup(monkeypatch, tmp_path):
    _create_installed_runtime(monkeypatch, tmp_path)
    (tmp_path / "runtime" / "Lib" / "site-packages" /
     "imageio_ffmpeg" / "binaries").rmdir()
    monkeypatch.setattr(launcher.shutil, "which", lambda *_: None)

    status, reason = launcher._runtime_status()

    assert status is launcher.RuntimeStatus.NEEDS_SETUP
    assert "FFmpeg" in reason


def test_inconclusive_probe_does_not_force_reinstall(monkeypatch, tmp_path):
    _create_installed_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 2),
    )
    status, _ = launcher._runtime_status()
    assert status is launcher.RuntimeStatus.UNVERIFIED


def test_missing_marker_triggers_installation(monkeypatch, tmp_path):
    _, _, marker = _create_installed_runtime(monkeypatch, tmp_path)
    marker.unlink()
    status, _ = launcher._runtime_status()
    assert status is launcher.RuntimeStatus.NEEDS_SETUP


def test_explicit_repair_opens_wizard_without_probe(monkeypatch, tmp_path):
    """A startup error can send the user directly into repair mode."""
    import sys
    import types

    monkeypatch.setattr(launcher.sys, "argv", ["WhisperXTranscriber.exe", "--repair"])
    monkeypatch.setattr(
        launcher, "_runtime_status",
        lambda: pytest.fail("Explicit repair must skip startup validation"),
    )
    monkeypatch.setattr(launcher, "_base_dir", lambda: str(tmp_path))
    wizard_arguments = []

    class FakeWizard:
        def __init__(self, **kwargs):
            wizard_arguments.append(kwargs)

        def run(self):
            wizard_arguments.append("run")

    monkeypatch.setitem(sys.modules, "setup_wizard", types.SimpleNamespace(SetupWizard=FakeWizard))
    launcher.main()

    assert wizard_arguments[0]["repair"] is True
    assert wizard_arguments[0]["reason"] == "Repair requested by user."
    assert wizard_arguments[0]["base_dir"] == str(tmp_path)
    assert wizard_arguments[1] == "run"


@pytest.mark.parametrize("returncode", [1, 2, -11])
def test_unexpected_probe_exit_logs_stderr_and_attempts_launch(monkeypatch, tmp_path, returncode):
    _create_installed_runtime(monkeypatch, tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["WhisperXTranscriber.exe"])
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, returncode, stderr=b"Traceback: metadata read failed\xff"),
    )
    launches = []
    monkeypatch.setattr(launcher, "_launch_app", lambda: launches.append(True))

    launcher.main()

    assert launches == [True]
    log = (tmp_path / "startup-warning.log").read_text(encoding="utf-8")
    assert str(returncode) in log
    assert "metadata read failed" in log


def test_real_probe_exception_does_not_open_setup(monkeypatch, tmp_path):
    import sys

    _, probe, _ = _create_installed_runtime(monkeypatch, tmp_path)
    probe.write_text('raise OSError("metadata read failed")\n', encoding="utf-8")
    monkeypatch.setattr(launcher.sys, "argv", ["WhisperXTranscriber.exe"])
    real_run = subprocess.run

    def run_with_test_python(command, **kwargs):
        # Exercise a real failing child interpreter, not a mocked return code.
        return real_run([sys.executable, *command[1:]], **kwargs)

    monkeypatch.setattr(launcher.subprocess, "run", run_with_test_python)
    launches = []
    monkeypatch.setattr(launcher, "_launch_app", lambda: launches.append(True))
    launcher.main()

    assert launches == [True]
    log = (tmp_path / "startup-warning.log").read_text(encoding="utf-8")
    assert "code 1" in log
    assert "Traceback" in log
    assert "OSError: metadata read failed" in log


def test_automatic_setup_does_not_request_destructive_repair(monkeypatch, tmp_path):
    import sys
    from types import SimpleNamespace

    arguments = []
    monkeypatch.setattr(launcher.sys, "argv", ["WhisperXTranscriber.exe"])
    monkeypatch.setattr(launcher, "_base_dir", lambda: str(tmp_path))
    monkeypatch.setattr(launcher, "_runtime_status",
                        lambda: (launcher.RuntimeStatus.NEEDS_SETUP, "Missing dependency"))

    def wizard(**kwargs):
        arguments.append(kwargs)
        return SimpleNamespace(run=lambda: None)

    monkeypatch.setitem(sys.modules, "setup_wizard", SimpleNamespace(SetupWizard=wizard))
    launcher.main()
    assert arguments[0]["repair"] is False

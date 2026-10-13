"""Regression tests for the thin PyInstaller launcher's child process environment."""

import os
import pytest

import launcher


@pytest.mark.parametrize("frozen", [True, False])
def test_launch_app_uses_runtime_tcl_tk_paths(monkeypatch, tmp_path, frozen):
    """An external Python must not inherit PyInstaller's incompatible Tcl/Tk data."""
    app_script = tmp_path / "app.py"
    app_script.write_text("# stub app\n", encoding="utf-8")
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
    assert launched["args"] == [str(runtime_py), str(app_script)]
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

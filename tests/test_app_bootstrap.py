"""Tests for reporting GUI startup failures in portable pythonw launches."""

import app_bootstrap


def test_bootstrap_runs_main_script(monkeypatch, tmp_path):
    bootstrap = tmp_path / "app_bootstrap.py"
    monkeypatch.setattr(app_bootstrap, "__file__", str(bootstrap))
    called = []

    def fake_run(path, **kwargs):
        called.append((path, kwargs))

    monkeypatch.setattr(app_bootstrap.runpy, "run_path", fake_run)

    assert app_bootstrap.main() == 0
    assert called == [(str(tmp_path / "app.py"), {"run_name": "__main__"})]


def test_bootstrap_logs_and_displays_startup_error(monkeypatch, tmp_path):
    monkeypatch.setattr(app_bootstrap, "__file__", str(tmp_path / "app_bootstrap.py"))
    messages = []

    def cannot_import(*_args, **_kwargs):
        raise ImportError("missing runtime dependency")

    monkeypatch.setattr(app_bootstrap.runpy, "run_path", cannot_import)
    monkeypatch.setattr(app_bootstrap, "_show_error", messages.append)

    assert app_bootstrap.main() == 1
    log = (tmp_path / "startup-error.log").read_text(encoding="utf-8")
    assert "ImportError: missing runtime dependency" in log
    assert len(messages) == 1
    assert "startup-error.log" in messages[0]

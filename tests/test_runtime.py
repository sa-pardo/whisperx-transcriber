"""Tests for CUDA driver detection without requiring an NVIDIA GPU."""
import subprocess

import pytest

from core import runtime


CUDA_TORCH_INDEX = "https://download.pytorch.org/whl/cu128"


@pytest.mark.parametrize(
    ("nvidia_smi_output", "expected"),
    [
        (
            "NVIDIA-SMI 595.97  Driver Version: 595.97  CUDA Version: 13.2",
            CUDA_TORCH_INDEX,
        ),
        (
            "NVIDIA-SMI 617.42  KMD Version: 617.42  CUDA UMD Version: 13.4",
            CUDA_TORCH_INDEX,
        ),
        ("CUDA Version: 12.8", CUDA_TORCH_INDEX),
        ("CUDA UMD Version: 12.8", CUDA_TORCH_INDEX),
        ("CUDA Version: 12.7", None),
        ("CUDA UMD Version: 12.7", None),
        ("NVIDIA-SMI 617.42  KMD Version: 617.42", None),
    ],
)
def test_cuda_torch_index_version_formats(monkeypatch, nvidia_smi_output, expected):
    def fake_run(command, **_kwargs):
        assert command == ["nvidia-smi"]
        return subprocess.CompletedProcess(command, 0, stdout=nvidia_smi_output)

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    assert runtime.cuda_torch_index() == expected


def test_cuda_torch_index_ignores_failed_nvidia_smi(monkeypatch):
    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 1, stdout="CUDA UMD Version: 13.4"
        ),
    )
    assert runtime.cuda_torch_index() is None


def test_cuda_torch_index_handles_missing_nvidia_smi(monkeypatch):
    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("nvidia-smi")

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    assert runtime.cuda_torch_index() is None


def test_quick_probe_avoids_importing_torch(monkeypatch):
    """Even a CUDA check must inspect metadata, not load torch native DLLs."""
    import builtins

    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)
    monkeypatch.setattr(runtime.metadata, "version", lambda name: "2.8.0+cu128")
    monkeypatch.setattr(runtime.util, "find_spec", lambda name: object())

    real_import = builtins.__import__

    def no_torch_import(name, *args, **kwargs):
        if name == "torch" or name.startswith("torch."):
            raise AssertionError("Quick check imported PyTorch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_torch_import)
    assert runtime.dependencies_ready(require_cuda=True, quick=True)


def test_quick_cuda_check_rejects_cpu_only_wheel(monkeypatch):
    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)
    monkeypatch.setattr(runtime.metadata, "version", lambda name: "2.8.0+cpu")
    assert not runtime.torch_ready(require_cuda=True, quick=True)


def test_quick_flag_selects_metadata_only_check(monkeypatch):
    calls = []
    monkeypatch.setattr(runtime.sys, "argv", ["runtime.py", "--quick"])
    monkeypatch.setattr(
        runtime, "dependencies_ready",
        lambda require_cuda, *, quick: calls.append((require_cuda, quick)) or True,
    )
    assert runtime.main() == 0
    assert calls == [(False, True)]


@pytest.mark.parametrize("torch_only", [False, True])
def test_missing_metadata_uses_dedicated_exit_code(monkeypatch, torch_only):
    def missing(_name):
        raise runtime.metadata.PackageNotFoundError("torch")

    monkeypatch.setattr(runtime.metadata, "version", missing)
    monkeypatch.setattr(runtime.sys, "argv",
                        ["runtime.py", "--quick"] + (["--torch-only"] if torch_only else []))
    assert runtime.main() == runtime.EXIT_NEEDS_SETUP == 10


@pytest.mark.parametrize("error", [OSError("metadata unreadable"), ValueError("bad metadata")])
def test_metadata_failure_is_not_missing_dependencies(monkeypatch, capsys, error):
    def broken(_name):
        raise error

    monkeypatch.setattr(runtime.metadata, "version", broken)
    monkeypatch.setattr(runtime.sys, "argv", ["runtime.py", "--quick"])
    assert runtime.main() == runtime.EXIT_PROBE_ERROR == 1
    assert str(error) in capsys.readouterr().err


@pytest.mark.parametrize("require_cuda", [False, True])
def test_quick_probe_never_imports_dependencies(monkeypatch, require_cuda):
    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)
    monkeypatch.setattr(runtime.metadata, "version", lambda name: "2.8.0+cu128")
    monkeypatch.setattr(runtime.util, "find_spec", lambda name: object())
    monkeypatch.setattr(runtime, "import_module",
                        lambda name: pytest.fail(f"Quick probe imported {name}"))
    assert runtime.dependencies_ready(require_cuda, quick=True)


def test_full_cpu_probe_imports_torch_packages(monkeypatch):
    from types import SimpleNamespace

    calls = []
    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)

    def import_package(name):
        calls.append(name)
        return SimpleNamespace(version=SimpleNamespace(cuda=None))

    monkeypatch.setattr(runtime, "import_module", import_package)
    assert runtime.torch_ready(require_cuda=False)
    assert calls == ["torch", "torchaudio", "torchvision"]


@pytest.mark.parametrize("broken_module", ["torch", "torchaudio", "torchvision"])
@pytest.mark.parametrize("error_type", [ImportError, OSError, RuntimeError])
def test_full_cpu_probe_rejects_broken_imports(monkeypatch, capsys, broken_module, error_type):
    from types import SimpleNamespace

    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)

    def import_package(name):
        if name == broken_module:
            raise error_type(f"corrupt {name}")
        return SimpleNamespace(version=SimpleNamespace(cuda=None))

    monkeypatch.setattr(runtime, "import_module", import_package)
    assert not runtime.torch_ready(require_cuda=False)
    assert f"corrupt {broken_module}" in capsys.readouterr().err


@pytest.mark.parametrize("cuda_version, expected", [(None, False), ("12.8", True)])
def test_full_cuda_probe_checks_build_without_requiring_driver(monkeypatch, cuda_version, expected):
    from types import SimpleNamespace

    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)
    monkeypatch.setattr(runtime, "import_module",
                        lambda name: SimpleNamespace(version=SimpleNamespace(cuda=cuda_version)))
    assert runtime.torch_ready(require_cuda=True) is expected


@pytest.mark.parametrize("broken_module", [None, "whisperx", "pyannote.audio", "torchcodec",
                                            "customtkinter", "PIL.Image", "imageio_ffmpeg"])
def test_full_probe_checks_core_imports(monkeypatch, broken_module):
    calls = []
    monkeypatch.setattr(runtime, "torch_ready", lambda *args, **kwargs: True)
    monkeypatch.setattr(runtime, "_versions_match", lambda versions: True)
    monkeypatch.setattr(runtime.util, "find_spec", lambda name: object())

    def import_package(name):
        calls.append(name)
        if name == broken_module:
            raise ImportError(f"corrupt {name}")
        return object()

    monkeypatch.setattr(runtime, "import_module", import_package)
    assert runtime.dependencies_ready() is (broken_module is None)
    if broken_module is None:
        assert calls == ["whisperx", "pyannote.audio", "torchcodec",
                         "customtkinter", "PIL.Image", "imageio_ffmpeg"]
    else:
        assert broken_module in calls

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

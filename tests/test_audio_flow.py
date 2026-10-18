"""Guard the predecoded-waveform contract without downloading ML models."""
import sys
from types import ModuleType

from core import pipeline


def test_diarization_receives_predecoded_audio_instead_of_file_path(monkeypatch):
    received = {}
    fake_diarize = ModuleType("whisperx.diarize")

    class StubDiarizationPipeline:
        def __init__(self, **kwargs):
            received["model_options"] = kwargs

        def __call__(self, audio, **kwargs):
            received["audio"] = audio
            received["diarization_options"] = kwargs
            return ["speaker-segments"]

    def assign_word_speakers(speakers, result):
        received["speakers"] = speakers
        return result

    fake_diarize.DiarizationPipeline = StubDiarizationPipeline
    fake_diarize.assign_word_speakers = assign_word_speakers

    fake_whisperx = ModuleType("whisperx")
    fake_whisperx.__path__ = []
    fake_whisperx.diarize = fake_diarize
    monkeypatch.setitem(sys.modules, "whisperx", fake_whisperx)
    monkeypatch.setitem(sys.modules, "whisperx.diarize", fake_diarize)
    monkeypatch.setattr(pipeline, "cleanup_memory", lambda: None)

    predecoded_audio = object()
    result = {"segments": []}
    assert pipeline.diarize(
        result, predecoded_audio, "cpu", "test-token", min_speakers=1,
        max_speakers=2,
    ) is result

    assert received["audio"] is predecoded_audio
    assert received["speakers"] == ["speaker-segments"]
    assert received["diarization_options"]["min_speakers"] == 1
    assert received["diarization_options"]["max_speakers"] == 2

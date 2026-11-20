from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from autogram.content.ai_caption import CaptionError, generate_caption


def install_fake_genai(monkeypatch, *, response_text="A real caption #gaming"):
    uploaded = SimpleNamespace(name="files/test-video", state=SimpleNamespace(name="ACTIVE"))
    calls = {"deleted": False, "uploaded": False}

    class FakeFiles:
        def upload(self, *, file):
            calls["uploaded"] = True
            return uploaded

        def get(self, *, name):
            return uploaded

        def delete(self, *, name):
            calls["deleted"] = True

    class FakeModels:
        def generate_content(self, *, model, contents):
            assert uploaded in contents
            return SimpleNamespace(text=response_text)

    fake_genai = SimpleNamespace(
        Client=lambda **kwargs: SimpleNamespace(files=FakeFiles(), models=FakeModels())
    )
    fake_google = types.ModuleType("google")
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    return calls


def test_generate_caption_uses_uploaded_video_and_cleans_up(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = install_fake_genai(monkeypatch)

    caption = generate_caption(b"video bytes", "clip.mp4")

    assert caption == "A real caption #gaming"
    assert calls["uploaded"]
    assert calls["deleted"]


def test_generate_caption_rejects_empty_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    install_fake_genai(monkeypatch, response_text="")

    with pytest.raises(CaptionError, match="empty caption"):
        generate_caption(b"video bytes", "clip.mp4")


def test_generate_caption_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(CaptionError, match="GEMINI_API_KEY"):
        generate_caption(b"video bytes", "clip.mp4")

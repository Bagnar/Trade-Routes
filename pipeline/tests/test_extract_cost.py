import json

from pipeline import extract


def test_unchanged_page_is_skipped_without_model_call(tmp_path):
    path = tmp_path / "ca-cbsa__abcdef12.json"
    path.write_text(json.dumps({"content_hash": "h1", "facts": []}), encoding="utf8")
    assert extract.unchanged_since_last_extract(path, "h1")
    assert not extract.unchanged_since_last_extract(path, "h2")
    assert not extract.unchanged_since_last_extract(tmp_path / "missing.json", "h1")


def test_extract_registry_respects_page_cap(monkeypatch, tmp_path):
    calls = []

    class FakeSource:
        id = "x"
        country = "CA"
        topics = ("t",)
        urls = ("https://a/1", "https://a/2", "https://a/3")

    monkeypatch.setattr(extract.registry, "load_sources", lambda: [FakeSource()])
    monkeypatch.setattr(extract, "_client", lambda: object())

    def fake_extract_url(url, topic=None, client=None, out_dir=None, force=False):
        calls.append(url)
        return tmp_path / f"{len(calls)}.json"

    monkeypatch.setattr(extract, "extract_url", fake_extract_url)
    written = extract.extract_registry(out_dir=tmp_path, max_pages=2)
    assert len(written) == 2 and calls == ["https://a/1", "https://a/2"]


def test_extract_registry_stops_on_credit_error(monkeypatch, tmp_path):
    class FakeSource:
        id = "x"
        country = "CA"
        topics = ("t",)
        urls = ("https://a/1", "https://a/2")

    monkeypatch.setattr(extract.registry, "load_sources", lambda: [FakeSource()])
    monkeypatch.setattr(extract, "_client", lambda: object())
    attempts = []

    def failing(url, **kw):
        attempts.append(url)
        raise RuntimeError("Your credit balance is too low to access the Anthropic API.")

    monkeypatch.setattr(extract, "extract_url", failing)
    assert extract.extract_registry(out_dir=tmp_path) == []
    assert attempts == ["https://a/1"]

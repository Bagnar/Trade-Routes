import json
from types import SimpleNamespace

import pytest

from pipeline import extract


def test_unchanged_page_is_skipped_without_model_call(tmp_path):
    path = tmp_path / "ca-cbsa__abcdef12.json"
    path.write_text(json.dumps({"content_hash": "h1", "facts": []}), encoding="utf8")
    assert extract.unchanged_since_last_extract(path, "h1")
    assert not extract.unchanged_since_last_extract(path, "h2")
    assert not extract.unchanged_since_last_extract(tmp_path / "missing.json", "h1")


def test_prices_and_batch_discount():
    assert extract.price_usd("claude-opus-5", 1_000_000, 0) == 5.0
    assert extract.price_usd("claude-opus-5", 0, 1_000_000) == 25.0
    assert extract.price_usd("claude-opus-5", 1_000_000, 1_000_000, batch=True) == 15.0
    assert extract.price_usd("unknown-model", 1_000_000, 0) == 5.0  # unknown = dearest


class FakeSource:
    def __init__(self, urls, country="CA"):
        self.id = "x"
        self.country = country
        self.topics = ("t",)
        self.urls = tuple(urls)


@pytest.fixture
def registry_of_three(monkeypatch, tmp_path):
    monkeypatch.setattr(extract.registry, "load_sources", lambda: [FakeSource(["https://a/1", "https://a/2", "https://a/3"])])
    monkeypatch.setattr(extract, "_client", lambda: object())
    return tmp_path


def test_extract_registry_respects_page_cap(monkeypatch, registry_of_three):
    tmp_path = registry_of_three
    calls = []

    def fake_extract_url(url, topic=None, client=None, out_dir=None, force=False, spend=None):
        calls.append(url)
        spend.add(SimpleNamespace(input_tokens=1000, output_tokens=100))
        return tmp_path / f"{len(calls)}.json"

    monkeypatch.setattr(extract, "extract_url", fake_extract_url)
    written = extract.extract_registry(out_dir=tmp_path, max_pages=2, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md")
    assert len(written) == 2 and calls == ["https://a/1", "https://a/2"]
    ledger = json.loads((tmp_path / "usage.json").read_text(encoding="utf8"))
    assert ledger["runs"][0]["pages"] == 2 and "PIPELINE_MAX_PAGES" in ledger["runs"][0]["note"]


def test_extract_registry_stops_on_credit_error(monkeypatch, registry_of_three):
    tmp_path = registry_of_three
    attempts = []

    def failing(url, **kw):
        attempts.append(url)
        raise RuntimeError("Your credit balance is too low to access the Anthropic API.")

    monkeypatch.setattr(extract, "extract_url", failing)
    assert extract.extract_registry(out_dir=tmp_path, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md") == []
    assert attempts == ["https://a/1"]


def test_run_cap_in_dollars_stops_before_the_next_call(monkeypatch, registry_of_three):
    tmp_path = registry_of_three
    monkeypatch.setattr(extract, "MAX_USD", 0.15)  # first call estimated ~0.13 $ fits; the second would not
    calls = []

    def fake_extract_url(url, topic=None, client=None, out_dir=None, force=False, spend=None):
        reason = spend.would_exceed(extract.estimate_usd(spend.model, "x" * 4000))
        if reason:
            spend.stop = reason
            return None
        calls.append(url)
        spend.add(SimpleNamespace(input_tokens=2000, output_tokens=1500))  # ~0.0475 $ on Opus
        return tmp_path / f"{len(calls)}.json"

    monkeypatch.setattr(extract, "extract_url", fake_extract_url)
    written = extract.extract_registry(out_dir=tmp_path, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md")
    assert len(written) == 1 and calls == ["https://a/1"]
    report = (tmp_path / "r.md").read_text(encoding="utf8")
    assert "PIPELINE_MAX_USD" in report


def test_monthly_cap_blocks_the_run_before_any_call(monkeypatch, registry_of_three):
    tmp_path = registry_of_three
    from datetime import date

    ledger = {"runs": [{"date": date.today().isoformat(), "usd": 14.9}], "pending_batch": None}
    (tmp_path / "usage.json").write_text(json.dumps(ledger), encoding="utf8")
    monkeypatch.setattr(extract, "MONTHLY_USD", 15.0)
    calls = []

    def fake_extract_url(url, topic=None, client=None, out_dir=None, force=False, spend=None):
        reason = spend.would_exceed(0.5)
        if reason:
            spend.stop = reason
            return None
        calls.append(url)
        return tmp_path / "1.json"

    monkeypatch.setattr(extract, "extract_url", fake_extract_url)
    assert extract.extract_registry(out_dir=tmp_path, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md") == []
    assert calls == [] and "monthly cap" in (tmp_path / "r.md").read_text(encoding="utf8")


def test_large_page_is_skipped_not_truncated(monkeypatch, tmp_path):
    monkeypatch.setattr(extract, "MAX_PAGE_CHARS", 100)
    monkeypatch.setattr(extract.registry, "find_source", lambda url: SimpleNamespace(id="x"))
    monkeypatch.setattr(extract.fetch, "fetch_url", lambda url, **kw: SimpleNamespace(text="y" * 500, content_hash="h", fetched_at="2026-09-12T00:00:00+00:00"))
    called = []
    monkeypatch.setattr(extract, "propose_facts", lambda *a, **k: called.append(1) or [])
    spend = extract.Spend()
    assert extract.extract_url("https://a/1", out_dir=tmp_path, spend=spend) is None
    assert called == [] and spend.skipped_large == ["https://a/1"]


class FakeBatches:
    """Message Batches API stand-in: one batch, ends after `polls_until_end` retrieve() calls."""

    def __init__(self, page_text, polls_until_end=1):
        self.page_text = page_text
        self.polls = 0
        self.polls_until_end = polls_until_end
        self.requests = None

    def create(self, requests):
        self.requests = requests
        return SimpleNamespace(id="msgbatch_1", processing_status="in_progress")

    def retrieve(self, batch_id):
        self.polls += 1
        return SimpleNamespace(processing_status="ended" if self.polls >= self.polls_until_end else "in_progress", request_counts=SimpleNamespace(processing=1))

    def results(self, batch_id):
        for r in self.requests:
            msg = SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text=json.dumps({"facts": [{"block": "import", "country": "CA", "hs_scope": [], "statement": {"ru": "Запрещено", "en": "x"}, "quote": "prohibited goods", "quote_lang": "en", "has_number": False}]}))],
                usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
            )
            yield SimpleNamespace(custom_id=r["custom_id"], result=SimpleNamespace(type="succeeded", message=msg))


def test_batch_mode_submits_once_writes_facts_and_charges_half_price(monkeypatch, tmp_path):
    text = "Some prohibited goods are listed here."
    monkeypatch.setattr(extract.registry, "load_sources", lambda: [FakeSource(["https://a/1", "https://a/2"])])
    monkeypatch.setattr(extract.fetch, "fetch_url", lambda url, **kw: SimpleNamespace(text=text, content_hash="h" + url[-1], fetched_at="2026-09-12T00:00:00+00:00"))
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    batches = FakeBatches(text)
    client = SimpleNamespace(messages=SimpleNamespace(batches=batches))
    written = extract.extract_registry(out_dir=tmp_path, batch=True, client=client, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md")
    assert len(written) == 2 and len(batches.requests) == 2
    assert batches.requests[0]["params"]["model"] == extract.MODEL and "<page>" in batches.requests[0]["params"]["messages"][0]["content"]
    ledger = json.loads((tmp_path / "usage.json").read_text(encoding="utf8"))
    run = ledger["runs"][0]
    assert run["batch"] is True and run["pages"] == 2 and run["facts"] == 2
    assert run["usd"] == pytest.approx(extract.price_usd(extract.MODEL, 2000, 400, batch=True))
    assert ledger["pending_batch"] is None
    doc = json.loads(written[0].read_text(encoding="utf8"))
    assert doc["facts"][0]["quote"] == "prohibited goods"


def test_batch_still_processing_is_remembered_and_collected_next_run(monkeypatch, tmp_path):
    text = "Some prohibited goods are listed here."
    monkeypatch.setattr(extract.registry, "load_sources", lambda: [FakeSource(["https://a/1"])])
    monkeypatch.setattr(extract.fetch, "fetch_url", lambda url, **kw: SimpleNamespace(text=text, content_hash="h1", fetched_at="2026-09-12T00:00:00+00:00"))
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    monkeypatch.setattr(extract, "BATCH_WAIT_MIN", 0)
    batches = FakeBatches(text, polls_until_end=2)
    client = SimpleNamespace(messages=SimpleNamespace(batches=batches))
    first = extract.extract_registry(out_dir=tmp_path, batch=True, client=client, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md")
    ledger = json.loads((tmp_path / "usage.json").read_text(encoding="utf8"))
    assert first == [] and ledger["pending_batch"]["id"] == "msgbatch_1" and ledger["runs"] == []
    assert "ещё обрабатывается" in (tmp_path / "r.md").read_text(encoding="utf8")
    # next run: the pending batch has ended; the page is unchanged so nothing new is submitted
    second = extract.extract_registry(out_dir=tmp_path, batch=True, client=client, ledger_path=tmp_path / "usage.json", report_path=tmp_path / "r.md")
    ledger = json.loads((tmp_path / "usage.json").read_text(encoding="utf8"))
    assert len(second) == 1 and ledger["pending_batch"] is None and ledger["runs"][0]["pages"] == 1

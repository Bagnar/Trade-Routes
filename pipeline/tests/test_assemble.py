import json

import pytest

from pipeline import assemble


@pytest.fixture(autouse=True)
def no_rates_on_disk(tmp_path, monkeypatch):
    # tests must not depend on data/rates/*.json loaded by the reference-data workflow
    monkeypatch.setattr(assemble.rates, "RATES_DIR", tmp_path)


FACTS = [
    {"block": "import", "country": "CA", "hs_scope": ["9897"], "statement": {"ru": "Товары принудительного труда запрещены", "en": ""},
     "quote": "prohibited from entering Canada", "quote_lang": "en", "url": "https://www.cbsa-asfc.gc.ca/d9-1-6.html", "source_id": "ca-cbsa", "fetched_at": "2026-09-12T11:45:00+00:00"},
    {"block": "cost", "country": "CA", "hs_scope": [], "statement": {"ru": "GST начисляется на стоимость плюс пошлину", "en": ""},
     "quote": "GST is calculated on", "quote_lang": "en", "url": "https://www.canada.ca/en/revenue-agency/x.html", "source_id": "ca-cra", "fetched_at": "2026-09-12T11:45:00+00:00"},
    {"block": "import", "country": "CA", "hs_scope": ["1001"], "statement": {"ru": "Пшеница: только для 1001", "en": ""},
     "quote": "wheat", "quote_lang": "en", "url": "https://www.cbsa-asfc.gc.ca/w.html", "source_id": "ca-cbsa", "fetched_at": "2026-09-12T11:45:00+00:00"},
    {"block": "export", "country": "CA", "hs_scope": [], "statement": {"ru": "Экспорт из Канады (не для страницы CN->CA)", "en": ""},
     "quote": "export", "quote_lang": "en", "url": "https://www.cbsa-asfc.gc.ca/e.html", "source_id": "ca-cbsa", "fetched_at": "2026-09-12T11:45:00+00:00"},
    {"block": "sanctions", "country": "US", "hs_scope": [], "statement": {"ru": "Санкции США (не эта пара)", "en": ""},
     "quote": "sanctions", "quote_lang": "en", "url": "https://ofac.treasury.gov/x", "source_id": "sanc-us-ofac", "fetched_at": "2026-09-12T11:45:00+00:00"},
]


def page():
    return {
        "corridor": {"from": {"code": "CN"}, "to": {"code": "CA"}},
        "product": {"hs6": "610910"},
        "status": {"sourcesTotal": 0, "sourcesMissing": 0, "lastChecked": "", "text": "old"},
        "summary": {"facts": [{"key": "Пошлина при ввозе", "text": "не загружена", "stamp": {"status": "none", "source": "rates", "label": "не загружена"}}]},
        "regime": {"facts": [{"text": "demo regime", "stamp": {"status": "ok", "source": "x", "label": "демо"}}]},
        "export": {"facts": []},
        "import": {"facts": [{"text": "demo import", "stamp": {"status": "none", "source": "x", "label": "не собрано"}}]},
        "logistics": {"facts": []},
        "sources": {"rows": [{"source": "x", "confirms": "demo", "checked": "—", "status": {"text": "демо", "kind": "warn"}}]},
    }


def test_scope_matching():
    assert assemble.scope_matches([], "610910")
    assert assemble.scope_matches(["61"], "610910") and assemble.scope_matches(["6109"], "610910")
    assert not assemble.scope_matches(["1001"], "610910")
    assert assemble.scope_matches(["9897"], "610910")  # Canadian special provision applies to all goods


def test_assemble_merges_matching_facts_and_keeps_placeholders():
    out = assemble.assemble_page(page(), FACTS)
    texts = [f["text"] for f in out["import"]["facts"]]
    assert texts[0] == "Товары принудительного труда запрещены" and "GST" in texts[1]
    assert "demo import" in texts and "Пшеница" not in " ".join(texts)
    assert all(f["text"] != "Экспорт из Канады (не для страницы CN->CA)" for f in out["export"]["facts"])
    assert all("США" not in f["text"] for f in out["regime"]["facts"])
    stamp = out["import"]["facts"][0]["stamp"]
    assert stamp["status"] == "ok" and stamp["url"].startswith("https://www.cbsa-asfc.gc.ca") and "12 сен 2026" in stamp["label"]
    assert out["import"]["facts"][0]["quote"] == "prohibited from entering Canada"
    assert out["sources"]["rows"][0]["source"] == "cbsa-asfc.gc.ca" and out["status"]["sourcesTotal"] == 2


def test_assemble_is_idempotent():
    once = assemble.assemble_page(page(), FACTS)
    twice = assemble.assemble_page(json.loads(json.dumps(once)), FACTS)
    assert len(twice["import"]["facts"]) == len(once["import"]["facts"])
    assert len(twice["sources"]["rows"]) == len(once["sources"]["rows"])


def test_rate_fact_uses_rates_layer(monkeypatch):
    monkeypatch.setattr(assemble.rates, "get_rate", lambda c, h, rates_dir=None: {"value": 18.0, "year": 2023, "source": "WITS", "url": "https://wits.worldbank.org/x", "fetched_at": "2026-09-12T12:00:00+00:00"})
    fact = assemble.rate_fact("CA", "610910")
    assert fact and "18%" in fact["text"] and fact["rate_ref"] == "CA:610910:import_mfn"
    monkeypatch.setattr(assemble.rates, "get_rate", lambda c, h, rates_dir=None: None)
    assert assemble.rate_fact("CA", "610910") is None

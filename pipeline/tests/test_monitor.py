import json
from datetime import date

from pipeline import monitor

URL = "https://www.cbsa-asfc.gc.ca/publications/dm-md/d9/d9-1-6-eng.html"


def make_page(tmp_path, quote):
    folder = tmp_path / "pages"
    folder.mkdir()
    doc = {
        "isDemo": False,
        "regime": {"facts": [{"text": "Импорт товаров принудительного труда запрещён", "quote": quote,
                              "stamp": {"status": "warn", "source": "cbsa-asfc.gc.ca", "label": "старое", "url": URL}}]},
        "summary": {"facts": [{"text": "без цитаты", "stamp": {"status": "note", "source": "x", "label": "оценка"}}]},
    }
    (folder / "p.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf8")
    return folder


def test_quote_still_present_confirms_fact(tmp_path):
    folder = make_page(tmp_path, "goods that are mined, manufactured or produced wholly or in part by forced labour")
    fetcher = lambda url: "The importation of goods that are mined, manufactured or produced wholly or in part by forced labour is prohibited."
    result = monitor.run([folder], today=date(2026, 9, 12), fetcher=fetcher)
    doc = json.loads((folder / "p.json").read_text(encoding="utf8"))
    stamp = doc["regime"]["facts"][0]["stamp"]
    assert result.confirmed == 1 and result.skipped_no_quote == 1
    assert stamp["status"] == "ok" and stamp["label"] == "проверено 12 сен 2026" and stamp["verifiedAt"] == "2026-09-12"


def test_missing_quote_flags_fact_for_review(tmp_path):
    folder = make_page(tmp_path, "this sentence is gone")
    result = monitor.run([folder], today=date(2026, 9, 12), fetcher=lambda url: "page rewritten")
    stamp = json.loads((folder / "p.json").read_text(encoding="utf8"))["regime"]["facts"][0]["stamp"]
    assert result.changed == 1 and stamp["status"] == "warn" and "требует проверки" in stamp["label"]


def test_unreachable_source_becomes_unavailable(tmp_path):
    folder = make_page(tmp_path, "anything")

    def fetcher(url):
        raise ConnectionError("down")

    result = monitor.run([folder], today=date(2026, 9, 12), fetcher=fetcher)
    stamp = json.loads((folder / "p.json").read_text(encoding="utf8"))["regime"]["facts"][0]["stamp"]
    assert result.unavailable == 1 and stamp["status"] == "none" and "недоступен" in stamp["label"]

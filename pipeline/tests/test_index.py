import json

from pipeline import index

FACTS = [
    {"block": "sanctions", "country": "US", "targets": ["IR"], "hs_scope": ["5701"], "statement": {"ru": "Запрещён ввоз ковров из Ирана."}, "quote": "x", "url": "https://ofac.treasury.gov/iran", "source_id": "sanc-us-ofac", "fetched_at": "2026-09-10T00:00:00Z"},
    {"block": "sanctions", "country": "US", "targets": ["RU"], "hs_scope": [], "statement": {"ru": "Ограничены расчёты."}, "quote": "x", "url": "https://ofac.treasury.gov/russia", "source_id": "sanc-us-ofac", "fetched_at": "2026-09-10T00:00:00Z"},
    {"block": "export_support", "country": "RU", "hs_scope": ["10"], "statement": {"ru": "Компенсация перевозки зерна."}, "quote": "x", "url": "https://mcx.gov.ru/x", "source_id": "ru-mcx", "fetched_at": "2026-09-10T00:00:00Z"},
]
PROGRAMS = [
    {"authority": "US", "domain": "ofac.treasury.gov", "url": "https://ofac.treasury.gov/iran", "targets": ["IR"]},
    {"authority": "US", "domain": "ofac.treasury.gov", "url": "https://ofac.treasury.gov/russia", "targets": ["RU"]},
]


def test_parts_without_data_have_no_score(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    # even with data/agreements.json on disk (the reference-data runner has it), an explicit None means "not loaded"
    monkeypatch.setattr(index.agreements, "load", lambda path=None: {"agreements": [{"name": "x", "members": ["CN", "CA"]}]})
    c = index.compute("CN", "CA", "610910", facts=[], programs=[], agreements_doc=None)
    assert all(p["score"] is None for p in c["parts"])
    assert c["of"] == 0 and c["verdict"].startswith("не рассчитано")
    assert c["agreement"] == "не проверено" and c["sanctions"] == "не проверено" and c["duty"] == "ставка не загружена"


def test_duty_from_rates_table_and_agreement_from_wto(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    (tmp_path / "CA.json").write_text(json.dumps({"country": "CA", "year": 2023, "url": "u", "fetched_at": "2026-09-12", "rates": {"610910": 18.0}}), encoding="utf8")
    doc = {"agreements": [{"name": "EAEU - Iran", "members": ["RU", "IR"], "type": "FTA", "in_force": "2025-05-15"}]}
    c = index.compute("CN", "CA", "610910", facts=[], programs=[], agreements_doc=doc)
    assert c["parts"][0]["score"] == 2 and "18%" in c["parts"][0]["basis"] and c["duty"] == "18%"
    assert c["agreement"] == "нет в базе РТС ВТО"
    assert c["total"] == 2 and c["of"] == 5
    assert index.compute("RU", "IR", "100199", facts=[], programs=[], agreements_doc=doc)["agreement"] == "EAEU - Iran"


def test_sanctions_are_an_obstacle_and_a_ban_zeroes_the_total(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    support_only = [FACTS[1], FACTS[2]]
    c = index.compute("RU", "IR", "100199", facts=support_only, programs=PROGRAMS, agreements_doc=None)
    assert c["parts"][1]["score"] == 2 and "US" in c["parts"][1]["basis"] and c["sanctions"] == "есть: US"
    assert c["parts"][2]["score"] == 3 and c["support"] == "1 стр."
    assert c["total"] == 5 and c["of"] == 10 and c["banned"] is False
    banned = index.compute("RU", "IR", "570110", facts=FACTS, programs=PROGRAMS, agreements_doc=None)
    assert banned["banned"] and banned["total"] == 0 and banned["parts"][1]["score"] == 0


def test_no_sanctions_is_never_claimed_without_checked_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    c = index.compute("CN", "CA", "610910", facts=[FACTS[1]], programs=PROGRAMS, agreements_doc=None)
    assert c["parts"][1]["score"] == 4 and "не называют" in c["parts"][1]["basis"]
    assert c["sanctions"] == "в проверенных программах нет"


def test_compare_rows_put_this_page_and_sort_by_score(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    (tmp_path / "CA.json").write_text(json.dumps({"country": "CA", "year": 2023, "url": "u", "fetched_at": "2026-09-12", "rates": {"610910": 18.0}}), encoding="utf8")
    (tmp_path / "TR.json").write_text(json.dumps({"country": "TR", "year": 2023, "url": "u", "fetched_at": "2026-09-12", "rates": {"610910": 0.0}}), encoding="utf8")
    rows = index.compare_rows("CN", "CA", "610910", facts=[])
    assert [r["to"] for r in rows] == ["Турция", "Канада — эта страница"]
    assert rows[1]["here"] is True and rows[0]["score"]["text"] == "5 из 5"


def test_country_wide_ban_wording_without_product_scope_is_an_obstacle_not_a_ban(tmp_path, monkeypatch):
    monkeypatch.setattr(index.rates, "RATES_DIR", tmp_path)
    gold = {"block": "sanctions", "country": "US", "targets": ["RU"], "hs_scope": [], "statement": {"ru": "США запретили импорт золота российского происхождения."}, "quote": "x", "url": "https://ofac.treasury.gov/russia", "source_id": "sanc-us-ofac", "fetched_at": "2026-09-10T00:00:00Z"}
    c = index.compute("CN", "RU", "610910", facts=[gold], programs=PROGRAMS, agreements_doc=None)
    assert c["banned"] is False and c["parts"][1]["score"] == 2

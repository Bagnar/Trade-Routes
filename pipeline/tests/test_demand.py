import json

from pipeline import demand


def test_total_value_picks_the_world_total_not_a_breakdown_row():
    body = json.dumps({"data": [
        {"partner2Code": 4, "customsCode": "C00", "motCode": 0, "primaryValue": 5.0},
        {"partner2Code": 0, "customsCode": "C00", "motCode": 0, "primaryValue": 123456.0},
        {"partner2Code": 0, "customsCode": "C01", "motCode": 0, "primaryValue": 99.0},
    ]})
    assert demand.total_value(body) == 123456.0
    assert demand.total_value(json.dumps({"data": []})) is None
    mirror = json.dumps({"data": [{"reporterCode": 1, "partner2Code": 0, "customsCode": "C00", "motCode": 0, "primaryValue": 10.0}, {"reporterCode": 2, "partner2Code": 0, "customsCode": "C00", "motCode": 0, "primaryValue": 5.0}]})
    assert demand.total_value(mirror, mirror=True) == 15.0


def _reply(value):
    return json.dumps({"data": [{"partner2Code": 0, "customsCode": "C00", "motCode": 0, "primaryValue": value}]}) if value else json.dumps({"data": []})


def test_loader_keeps_three_recent_years_and_reader_computes_growth(tmp_path, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    monkeypatch.setattr(demand, "DEMAND_DIR", tmp_path)
    monkeypatch.setattr(demand, "PACE_SECONDS", 0)
    values = {"2025": 677e6, "2024": 654e6, "2023": 600e6, "2022": 590e6}
    calls = []

    def fake_fetch(url, **kw):
        calls.append(url)
        year = url.split("period=")[1].split("&")[0]
        return SimpleNamespace(http_status=200, html=_reply(values.get(year)), text="")

    monkeypatch.setattr(demand.fetch, "fetch_url", fake_fetch)
    assert demand.load(["CA"], ["610910"], today=date(2026, 9, 13)) == 1
    assert len(calls) == 3  # stops after three years with values
    d = demand.get_demand("CA", "610910", tmp_path, today=date(2026, 9, 13))
    assert d["latest_year"] == 2025 and d["value"] == 677e6 and d["growth_pct"] == 13 and d["span_years"] == 2
    assert d["kind"] == "reported" and d["stale"] is False
    # second load within 30 days: cache, no calls
    calls.clear()
    assert demand.load(["CA"], ["610910"], today=date(2026, 9, 20)) == 0 and calls == []


def test_mirror_fallback_and_call_budget(tmp_path, monkeypatch):
    from datetime import date
    from types import SimpleNamespace

    monkeypatch.setattr(demand, "DEMAND_DIR", tmp_path)
    monkeypatch.setattr(demand, "PACE_SECONDS", 0)

    def fake_fetch(url, **kw):
        if "flowCode=X" in url and "period=2025" in url:
            return SimpleNamespace(http_status=200, html=_reply(10e6), text="")
        return SimpleNamespace(http_status=200, html=_reply(None), text="")

    monkeypatch.setattr(demand.fetch, "fetch_url", fake_fetch)
    assert demand.load(["IR"], ["610910"], today=date(2026, 9, 13)) == 1
    d = demand.get_demand("IR", "610910", tmp_path, today=date(2026, 9, 13))
    assert d["kind"] == "mirror" and d["partners"] == len(demand.MIRROR_PARTNERS) and d["value"] == 10e6 * len(demand.MIRROR_PARTNERS)
    # budget: one call allowed -> nothing written for a new pair
    assert demand.load(["CA"], ["610910"], max_calls=1, today=date(2026, 9, 13)) == 0
    assert demand.get_demand("CA", "610910", tmp_path) is None


def test_stale_data_gets_no_score(tmp_path, monkeypatch):
    from datetime import date

    (tmp_path / "RU.json").write_text(json.dumps({"country": "RU", "series": {"610910": {"years": {"2021": 588e6, "2020": 433e6}, "kind": "reported", "partners": 0, "fetched_at": "2026-09-13T00:00:00+00:00"}}}), encoding="utf8")
    d = demand.get_demand("RU", "610910", tmp_path, today=date(2026, 9, 13))
    assert d["stale"] is True and d["latest_year"] == 2021
    from pipeline import index

    monkeypatch.setattr(demand, "DEMAND_DIR", tmp_path)
    score, basis = index.demand_part("RU", "610910")
    assert score is None and "старше" in basis
    (tmp_path / "CA.json").write_text(json.dumps({"country": "CA", "series": {"610910": {"years": {"2025": 677e6, "2023": 600e6}, "kind": "reported", "partners": 0, "fetched_at": "2026-09-13T00:00:00+00:00"}}}), encoding="utf8")
    score, basis = index.demand_part("CA", "610910")
    assert score == 5 and "677 млн USD" in basis and "ориентир" in basis

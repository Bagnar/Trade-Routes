from pipeline import validate

OK = {"status": "ok", "source": "cbsa-asfc.gc.ca", "label": "проверено 5 сен 2026", "url": "https://www.cbsa-asfc.gc.ca/x.html"}


def page(**over):
    doc = {"isDemo": False, "regime": {"facts": []}}
    doc.update(over)
    return doc


def test_verified_fact_without_quote_is_rejected():
    doc = page(regime={"facts": [{"text": "Импорт запрещён", "stamp": OK}]})
    rules = {v.rule for v in validate.check_quotes(doc, "p")}
    assert rules == {"quotes"}


def test_verified_fact_with_quote_and_url_passes():
    doc = page(regime={"facts": [{"text": "Импорт запрещён", "quote": "is prohibited", "stamp": OK}]})
    assert validate.check_quotes(doc, "p") == []


def test_url_outside_whitelist_is_rejected():
    bad = dict(OK, url="https://broker.example.com/x")
    doc = page(regime={"facts": [{"text": "x", "quote": "x", "stamp": bad}]})
    assert [v.rule for v in validate.check_whitelist(doc, "p")] == ["whitelist"]


def test_rate_number_without_rate_ref_is_rejected_on_real_pages():
    doc = page(regime={"facts": [{"text": "Пошлина 18% от стоимости", "quote": "18%", "stamp": OK}]})
    assert [v.rule for v in validate.check_numbers(doc, "p")] == ["numbers"]
    doc["regime"]["facts"][0]["rate_ref"] = "CA:610910:import_mfn"
    assert validate.check_numbers(doc, "p") == []


def test_demo_pages_may_carry_illustrative_numbers():
    doc = page(isDemo=True, regime={"facts": [{"text": "Пошлина 18%", "stamp": OK}]})
    assert validate.check_numbers(doc, "p") == []


def test_circumvention_wording_is_rejected_for_sanctioned_pairs():
    doc = page(
        sanctions={"tag": "Санкционный коридор", "text": "Обе страны под санкциями."},
        regime={"facts": [{"text": "Расчёты можно провести через дружественный банк третьей страны", "stamp": OK}]},
    )
    assert [v.rule for v in validate.check_circumvention(doc, "p")] == ["circumvention"]


def test_policy_sentence_is_allowed():
    doc = page(
        sanctions={"tag": "Санкционный коридор", "text": "Страница показывает ограничения как есть и не подсказывает, как их обойти."},
        regime={"facts": []},
    )
    assert validate.check_circumvention(doc, "p") == []


def test_all_shipped_pages_pass_validation():
    assert validate.validate_dirs() == []

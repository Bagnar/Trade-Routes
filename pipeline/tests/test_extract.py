from pipeline import extract

PAGE = "Goods produced wholly or in part by forced labour are prohibited. The rate of duty is 18%."


def test_accepts_only_facts_with_verbatim_quotes():
    candidates = [
        {"block": "regime", "country": "CA", "statement": {"ru": "Запрещён ввоз", "en": "Import prohibited"},
         "quote": "produced wholly or in part by forced labour are prohibited", "quote_lang": "en"},
        {"block": "regime", "country": "CA", "statement": {"ru": "Выдумано", "en": "Made up"},
         "quote": "this text is not on the page", "quote_lang": "en"},
        {"block": "import", "country": "CA", "statement": {"ru": "Без цитаты"}, "quote": ""},
        {"block": "nonsense", "country": "CA", "statement": {"ru": "x"}, "quote": "rate of duty"},
    ]
    kept, dropped = extract.accept_facts(candidates, PAGE)
    assert len(kept) == 1 and dropped == 3
    assert kept[0]["quote"].startswith("produced wholly")


def test_circumvention_advice_is_dropped():
    candidates = [{"block": "sanctions", "country": "RU", "statement": {"ru": "Платите через дружественный банк"},
                   "quote": "forced labour are prohibited", "quote_lang": "en"}]
    kept, dropped = extract.accept_facts(candidates, PAGE)
    assert kept == [] and dropped == 1


def test_json_parsing_tolerates_prose_around_object():
    assert extract._parse_json('Here you go:\n{"facts": [{"a": 1}]}\nDone.') == {"facts": [{"a": 1}]}
    assert extract._parse_json("no json here") == {"facts": []}

from pipeline import reference


def test_parse_h6_keeps_six_digit_codes_and_strips_prefix():
    payload = {"results": [
        {"id": "01", "text": "01 - Animals; live", "parent": "TOTAL"},
        {"id": "0101", "text": "0101 - Horses, asses, mules and hinnies; live"},
        {"id": "010121", "text": "010121 - Horses; live, pure-bred breeding animals"},
        {"id": "610910", "text": "610910 - T-shirts, singlets and other vests; of cotton, knitted or crocheted"},
    ]}
    rows = reference.parse_h6(payload)
    assert [r["code"] for r in rows] == ["010121", "610910"]
    assert rows[0]["en"].startswith("Horses; live") and rows[0]["ru"] == ""


def test_parse_ru_tnved_accepts_ten_and_six_digit_lines():
    text = "6109 10 000 0;Футболки, майки и прочие нательные фуфайки трикотажные, из хлопчатобумажной пряжи\n610990;Из прочих текстильных материалов\nmumbo jumbo"
    ru = reference.parse_ru_tnved(text)
    assert ru["610910"].startswith("Футболки") and ru["610990"].startswith("Из прочих")

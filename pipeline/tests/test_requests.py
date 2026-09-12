import json

from pipeline import requests as rq

BODY = """### Товар

дроны, 880622

### Откуда (страна или код ISO)

Китай

### Куда (страна или код ISO)

kz

### Режим

посылки покупателям
"""


def test_parse_issue_form_body():
    p = rq.parse_issue("Коридор: дроны", BODY)
    assert p == {"product": "дроны", "hs6": "880622", "from": "CN", "to": "KZ", "modes": ["parcel"]}


def test_parse_free_text_title_and_missing_code():
    p = rq.parse_issue("Коридор: тракторы 870190 из Германии в Узбекистан")
    assert p["from"] == "DE" and p["to"] == "UZ" and p["hs6"] == "870190"
    p = rq.parse_issue("Коридор: что-то из Атлантиды в Канаду")
    assert p["from"] is None and p["to"] == "CA" and p["hs6"] is None


def test_blank_page_has_only_placeholders_and_apply_creates_it(tmp_path):
    page = rq.blank_page("CN", "KZ", "880622", "дроны", ["parcel"])
    assert page["isDemo"] is False and page["product"]["hsLabel"] == "HS 8806.22"
    for section in ("regime", "export", "exportControl", "import", "logistics"):
        assert all(f["stamp"]["status"] in ("none", "note") for f in page[section]["facts"])
    assert page["sources"]["rows"] == [] and page["rating"]["parts"] == []
    queue = tmp_path / "requests.json"
    queue.write_text(json.dumps([
        {"issue": 1, "product": "дроны", "hs6": "880622", "from": "CN", "to": "KZ", "modes": ["b2b"], "status": "queued"},
        {"issue": 2, "product": "что-то", "hs6": None, "from": None, "to": "CA", "modes": ["b2b"], "status": "queued"},
    ]), encoding="utf8")
    pages = tmp_path / "pages"
    pages.mkdir()
    assert rq.apply(queue, pages) == 1
    items = json.loads(queue.read_text(encoding="utf8"))
    assert items[0]["status"] == "page_created" and items[0]["page"] == "/corridor/cn-kz/880622"
    assert items[1]["status"] == "needs_person"
    assert (pages / "cn-kz-880622-ru.json").exists()

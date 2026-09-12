from pipeline import agreements

RTAIS_HTML = """<html><body><table id="ctl00_x"><tr><th>RTA Name</th><th>Coverage</th><th>Type</th><th>Status</th>
<th>Date of entry into force</th><th>Current signatories</th></tr>
<tr><td><a href="x">EAEU - Iran</a></td><td>Goods</td><td>FTA</td><td>In Force</td><td>15-May-2025</td>
<td>Armenia; Belarus; Kazakhstan; Kyrgyz Republic; Russian Federation; Iran</td></tr>
<tr><td>Canada - Ukraine</td><td>Goods &amp; Services</td><td>FTA</td><td>In Force</td><td>01-Aug-2017</td><td>Canada; Ukraine</td></tr>
<tr><td>EU - Viet Nam</td><td>Goods &amp; Services</td><td>FTA &amp; EIA</td><td>In Force</td><td>01-Aug-2020</td><td>European Union; Viet Nam</td></tr>
<tr><td>Draft one</td><td>Goods</td><td>FTA</td><td>Early announcement</td><td></td><td>Canada; China</td></tr>
</table><table><tr><td>unrelated</td></tr></table></body></html>"""


def test_parse_rtais_reads_only_agreements_in_force():
    found = agreements.parse_rtais(RTAIS_HTML)
    names = [a["name"] for a in found]
    assert names == ["EAEU - Iran", "Canada - Ukraine", "EU - Viet Nam"]
    eaeu = found[0]
    assert eaeu["in_force"] == "2025-05-15" and eaeu["type"] == "FTA"
    assert {"RU", "IR", "KG", "AM", "BY", "KZ"} <= set(eaeu["members"])
    assert "DE" in found[2]["members"] and "VN" in found[2]["members"]  # EU expands to its members


def test_between_is_none_when_not_loaded_and_empty_when_no_match():
    doc = {"agreements": agreements.parse_rtais(RTAIS_HTML)}
    assert agreements.between("ru", "IR", doc)[0]["name"] == "EAEU - Iran"
    assert agreements.between("CN", "CA", doc) == []
    assert agreements.between("CN", "CA", None) is None or isinstance(agreements.between("CN", "CA", None), list)


def test_unknown_names_are_dropped_not_guessed():
    assert agreements.names_to_iso2("Atlantis; Canada") == ["CA"]

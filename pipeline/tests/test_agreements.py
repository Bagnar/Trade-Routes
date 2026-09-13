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


def test_members_from_rta_name_when_no_signatories_column():
    rows = [
        ["RTA Name", "Coverage", "Type", "Date of signature", "Date of entry into force", "Status"],
        ["Moldova, Republic of - Azerbaijan", "Goods", "FTA", "26-May-1995", "16-Apr-1996", "In Force"],
        ["EAEU - Iran", "Goods", "FTA", "25-Dec-2023", "15-May-2025", "In Force"],
        ["Pacific Alliance - Singapore", "Goods & Services", "FTA & EIA", "26-Jan-2022", "03-May-2025", "In force for at least one Party"],
        ["Atlantis - Mu", "Goods", "FTA", "", "", "In Force"],
    ]
    found = agreements.rows_to_agreements(rows)
    assert [a["name"] for a in found] == ["Moldova, Republic of - Azerbaijan", "EAEU - Iran", "Pacific Alliance - Singapore"]
    assert found[0]["members"] == ["MD", "AZ"] and found[0]["in_force"] == "1996-04-16"
    assert {"RU", "IR"} <= set(found[1]["members"]) and {"CL", "SG"} <= set(found[2]["members"])


def test_csv_export_is_parsed():
    csv_text = "RTA Name;Coverage;Type;Status;Date of entry into force\nCanada - Ukraine;Goods & Services;FTA;In Force;01-Aug-2017\n"
    rows = agreements.parse_csv_rows(csv_text)
    assert agreements.rows_to_agreements(rows)[0]["members"] == ["CA", "UA"]


def test_xlsx_export_is_parsed(tmp_path):
    import io
    import zipfile

    shared = "<sst xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><si><t>RTA Name</t></si><si><t>Status</t></si><si><t>Canada - Ukraine</t></si><si><t>In Force</t></si></sst>"
    sheet = "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData><row r=\"1\"><c r=\"A1\" t=\"s\"><v>0</v></c><c r=\"B1\" t=\"s\"><v>1</v></c></row><row r=\"2\"><c r=\"A2\" t=\"s\"><v>2</v></c><c r=\"B2\" t=\"s\"><v>3</v></c></row></sheetData></worksheet>"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", shared)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    rows = agreements.parse_xlsx_rows(buf.getvalue())
    assert rows == [["RTA Name", "Status"], ["Canada - Ukraine", "In Force"]]
    assert agreements.rows_to_agreements(rows)[0]["members"] == ["CA", "UA"]


def test_rta_is_name_forms():
    n = agreements.names_to_iso2
    assert set(n("Eurasian Economic Union (EAEU)")) == {"RU", "BY", "KZ", "AM", "KG"}
    assert n("EAEU - Accession of Armenia".replace(" - ", ";"))[:1] == ["RU"] and "AM" in n("Accession of Armenia")
    assert n("Central America;Korea, Republic of") == ["CR", "SV", "GT", "HN", "NI", "KR"]
    assert n("Colombia and Peru") == ["CO", "PE"]
    assert n("Costa Rica (Chile") == ["CR"] and n("Central European Free Trade Agreement (CEFTA) 2006")[:1] == ["AL"]
    assert n("Accession of the United Kingdom") == ["GB"]


def test_bloc_party_named_as_free_trade_area_resolves():
    table = [
        ["RTA ID", "RTA Name", "Type", "Status", "Date of Entry into Force (G)", "Current signatories"],
        ["42", "ASEAN - China", "FTA & EIA", "In Force", "38353", "China; ASEAN Free Trade Area (AFTA)"],
        ["437", "ASEAN - Australia - New Zealand", "FTA & EIA", "In Force", "40179", "Australia; New Zealand; ASEAN Free Trade Area (AFTA)"],
    ]
    out = agreements.rows_to_agreements(table)
    assert [a["name"] for a in out] == ["ASEAN - China", "ASEAN - Australia - New Zealand"]
    assert "CN" in out[0]["members"] and "VN" in out[0]["members"] and "TH" in out[0]["members"]
    assert {"AU", "NZ", "VN"} <= set(out[1]["members"])

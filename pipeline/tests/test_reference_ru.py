from pipeline import reference

ROWS = [
    ["Код ТН ВЭД", "Наименование позиции", "Доп. ед. изм.", "Ставка"],
    ["6109", "Майки, фуфайки с рукавами и прочие нательные фуфайки, трикотажные машинного или ручного вязания:", "", ""],
    ["6109 10 000 0", "– из хлопчатобумажной пряжи", "шт", "10"],
    ["6109 90", "– из прочих текстильных материалов:", "", ""],
    ["6109 90 200 0", "– – из шерстяной пряжи или пряжи из тонкого волоса животных или из химических волокон", "шт", "10"],
    ["6109 90 900 0", "– – прочие", "шт", "10"],
    ["8806", "Беспилотные летательные аппараты:", "", ""],
    ["8806 22 000 0", "– – с максимальной взлетной массой более 250 г, но не более 7 кг", "шт", "5"],
]


def test_ett_rows_give_hs6_russian_names():
    names = reference.parse_ett_rows(ROWS)
    assert names["610910"].startswith("Майки, фуфайки") and names["610910"].endswith(": из хлопчатобумажной пряжи")
    assert names["610990"].endswith(": из прочих текстильных материалов")
    assert names["880622"].endswith(": с максимальной взлетной массой более 250 г, но не более 7 кг")


def test_ett_page_links_are_recognised():
    html = '<a href="/upload/files/ett_2026.xlsx">ЕТТ ЕАЭС (xlsx)</a> <a href="/news/1">Новости</a> <a href="doc.pdf">Решение № 80</a>'
    files = reference.find_ett_files(html, "https://eec.eaeunion.org/comission/department/catr/ett/")
    assert files[0][0] == "https://eec.eaeunion.org/upload/files/ett_2026.xlsx"
    assert all("news" not in f[0] for f in files)


def test_ett_pdf_lines_are_parsed_with_continuations_and_rate_columns():
    lines = [
        "Код ТН ВЭД Наименование позиции Доп. ед. изм. Ставка ввозной таможенной пошлины",
        "6109 Майки, фуфайки с рукавами и прочие нательные фуфайки, трикотажные",
        "машинного или ручного вязания:",
        "6109 10 000 0 – из хлопчатобумажной пряжи шт 10",
        "6109 90 – из прочих текстильных материалов:",
        "6109 90 200 0 – – из шерстяной пряжи или пряжи из тонкого волоса животных или",
        "из химических волокон шт 10",
        "6109 90 900 0 – – прочие шт 10",
    ]
    names = reference.parse_ett_pdf_lines(lines)
    assert names["610910"] == "Майки, фуфайки с рукавами и прочие нательные фуфайки, трикотажные машинного или ручного вязания: из хлопчатобумажной пряжи"
    assert names["610990"].endswith(": из прочих текстильных материалов")
    assert reference.chapter_pdfs([("https://eec.eaeunion.org/upload/files/catr/ett/ru.61_2022_25.04.2022.pdf", "x"), ("https://x/ru.88_2022.pdf", "y"), ("https://x/other.pdf", "z")]) == {"61": "https://eec.eaeunion.org/upload/files/catr/ett/ru.61_2022_25.04.2022.pdf", "88": "https://x/ru.88_2022.pdf"}

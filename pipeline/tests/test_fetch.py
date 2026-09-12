import pytest

from pipeline import fetch

HTML = """<html><head><title>T</title><style>p{}</style><script>var x=1;</script></head>
<body><h1>Customs Tariff</h1><p>Goods  produced by forced labour are <b>prohibited</b>.</p>
<p>Rate of duty: 18%</p></body></html>"""


def test_html_to_text_drops_markup_and_scripts():
    text = fetch.html_to_text(HTML)
    assert "var x" not in text and "<b>" not in text
    assert "Goods produced by forced labour are prohibited." in text


def test_quote_check_ignores_whitespace_and_case():
    text = fetch.html_to_text(HTML)
    assert fetch.quote_in_text("goods produced by forced labour are PROHIBITED", text)
    assert not fetch.quote_in_text("goods produced by forced labour are allowed", text)


def test_fetch_refuses_urls_outside_whitelist():
    with pytest.raises(fetch.NotWhitelisted):
        fetch.fetch_url("https://some-broker.example.com/rates", save=False)

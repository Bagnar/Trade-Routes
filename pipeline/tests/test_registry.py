from pipeline import registry


def test_official_domain_is_allowed():
    assert registry.is_allowed("https://www.cbsa-asfc.gc.ca/publications/dm-md/d9/d9-1-6-eng.html")
    assert registry.is_allowed("https://mcx.gov.ru/ministry/departments/")


def test_path_prefix_is_enforced():
    # canada.ca is whitelisted only under the CRA and Health Canada prefixes
    assert registry.is_allowed("https://www.canada.ca/en/revenue-agency/services/tax.html")
    assert not registry.is_allowed("https://www.canada.ca/en/news/some-press-release.html")


def test_blogs_brokers_and_lookalikes_are_refused():
    for url in (
        "https://customs-broker-blog.example.com/duties",
        "https://cbsa-asfc.gc.ca.evil.example/",
        "https://forum.example.org/how-to-import",
    ):
        assert not registry.is_allowed(url)


def test_registry_loads_all_sections():
    sources = registry.load_sources()
    ids = {s.id for s in sources}
    assert {"ca-cbsa", "cn-mofcom", "ru-fts", "ir-irica", "sanc-us-ofac", "un-comtrade", "wassenaar", "us-bis"} <= ids


def test_data_files_are_not_extractor_pages():
    urls = [u for s in registry.load_sources() for u in s.urls]
    assert not any(u.endswith("H6.json") for u in urls)  # reference file: extract: false
    assert registry.is_allowed("https://comtradeapi.un.org/files/v1/app/reference/H6.json")  # still whitelisted for the loader

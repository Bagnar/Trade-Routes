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

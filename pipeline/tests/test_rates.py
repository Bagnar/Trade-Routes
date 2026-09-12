from pipeline import rates

SDMX = """<?xml version="1.0"?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message" xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
 <message:DataSet>
  <generic:Series>
   <generic:SeriesKey>
    <generic:Value id="REPORTER" value="124"/><generic:Value id="PARTNER" value="000"/>
    <generic:Value id="PRODUCTCODE" value="610910"/><generic:Value id="INDICATOR" value="AHS-SMPL-AVRG"/>
   </generic:SeriesKey>
   <generic:Obs><generic:ObsDimension value="2023"/><generic:ObsValue value="18"/></generic:Obs>
  </generic:Series>
  <generic:Series>
   <generic:SeriesKey>
    <generic:Value id="PRODUCTCODE" value="610910"/><generic:Value id="INDICATOR" value="AHS-WGHTD-AVRG"/>
   </generic:SeriesKey>
   <generic:Obs><generic:ObsDimension value="2023"/><generic:ObsValue value="17.2"/></generic:Obs>
  </generic:Series>
  <generic:Series>
   <generic:SeriesKey>
    <generic:Value id="PRODUCTCODE" value="6109"/><generic:Value id="INDICATOR" value="AHS-SMPL-AVRG"/>
   </generic:SeriesKey>
   <generic:Obs><generic:ObsDimension value="2023"/><generic:ObsValue value="18"/></generic:Obs>
  </generic:Series>
 </message:DataSet>
</message:GenericData>"""


def test_parse_wits_keeps_simple_average_hs6_only():
    rates_map, year = rates.parse_wits_sdmx(SDMX)
    assert rates_map == {"610910": 18.0} and year == 2023


def test_get_rate_reads_file(tmp_path):
    (tmp_path / "CA.json").write_text('{"country":"CA","year":2023,"source":"WITS","url":"u","fetched_at":"t","rates":{"610910":18.0}}', encoding="utf8")
    assert rates.get_rate("ca", "610910", tmp_path)["value"] == 18.0
    assert rates.get_rate("ca", "999999", tmp_path) is None
    assert rates.get_rate("xx", "610910", tmp_path) is None


STRUCTURE_SPECIFIC = """<?xml version="1.0" encoding="utf-8"?><message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"><message:DataSet DATASOURCE="TRN"><Series FREQ="A" DATATYPE="Reported" PRODUCTCODE="010121" PARTNER="000" REPORTER="124"><Obs TIME_PERIOD="2023" OBS_VALUE="0" TARIFFTYPE="MFN" OBS_VALUE_MEASURE="SimpleAverage" NOMENCODE="H6" /></Series><Series FREQ="A" DATATYPE="Reported" PRODUCTCODE="610910" PARTNER="000" REPORTER="124"><Obs TIME_PERIOD="2023" OBS_VALUE="18" TARIFFTYPE="MFN" OBS_VALUE_MEASURE="SimpleAverage" NOMENCODE="H6" /></Series><Series FREQ="A" DATATYPE="Reported" PRODUCTCODE="610910" PARTNER="000" REPORTER="124"><Obs TIME_PERIOD="2023" OBS_VALUE="5" TARIFFTYPE="PRF" OBS_VALUE_MEASURE="SimpleAverage" /></Series></message:DataSet></message:StructureSpecificData>"""


def test_parse_wits_structure_specific_layout():
    rates_map, year = rates.parse_wits_sdmx(STRUCTURE_SPECIFIC)
    assert rates_map == {"010121": 0.0, "610910": 18.0}  # the PRF series is not an MFN rate
    assert year == 2023

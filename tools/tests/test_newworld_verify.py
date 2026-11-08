"""tools/newworld/verify.py: a group that cannot run is a FAIL row naming why, never a crash; the table renders."""
from tools.newworld import verify as v


def test_section_turns_errors_into_fail_rows():
    rep = v.Report()

    @v.section(rep, "lod")
    def _a():
        raise FileNotFoundError("files.txt")

    @v.section(rep, "map")
    def _b():
        raise SystemExit("land manifest and landcover differ")

    @v.section(rep, "land")
    def _c():
        rep.row("land", "every cell has LAND", "3/3", True)

    assert [r["result"] for r in rep.rows] == ["FAIL", "FAIL", "PASS"]
    assert "files.txt" in rep.rows[0]["detail"] and "differ" in rep.rows[1]["detail"]
    md = rep.md()
    assert "1 PASS, 2 FAIL of 3" in md and "| land | every cell has LAND | 3/3 | **PASS** |" in md


def test_nif_textures_and_flow_names():
    raw = b"\x00\x05\x00\x00\x00textures\\landscape\\a.dds\x00junk\x01Data\\Textures\\b_n.DDS"
    assert v.nif_textures(raw) == {"textures\\landscape\\a.dds", "data\\textures\\b_n.dds"}
    assert v.FLOW.search("RiverWaterFlowNE") and v.FLOW.search("ANW_CreekWaterFlowNW") and not v.FLOW.search("DefaultMarshWater")

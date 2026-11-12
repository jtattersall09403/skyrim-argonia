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


def test_ecology_rows(tmp_path):
    eco, d = tmp_path / "plugin/ecology", tmp_path / "dump"
    eco.mkdir(parents=True)
    d.mkdir()
    rep = v.Report()
    v.ecology_rows(rep, tmp_path / "plugin", d)
    assert rep.rows[0]["value"] == "no ecology" and rep.rows[0]["result"] == "PASS"
    (eco / "actors.json").write_text('{"actors":[{"name":"a","level":7}]}')
    (eco / "cy+001.jsonl").write_text('{"actor":"a","fid":"F00001","x":4100.0,"y":10.0,"z":5.0}\n')
    (d / "ecology.tsv").write_text("cx\\tcy\\tfid\\tx\\ty\\tz\\trz\\tbase\\tbase_edid\\tsig\n".replace("\\t", "\t")
                                   + "1\t0\tF00001\t4100.5\t10\t5\t0\tK\tANW_Eco_x\tNpc\n")
    (d / "eco_npcs.tsv").write_text("edid\tkey\tlevel_kind\tlevel\tstats_template\tautocalc\nANW_Eco_x\tK\tfixed\t7\tFalse\tFalse\n")
    rep = v.Report()
    v.ecology_rows(rep, tmp_path / "plugin", d)
    assert all(r["result"] == "PASS" for r in rep.rows), rep.md()


def test_ecology_critter_rows(tmp_path):
    eco, d = tmp_path / "plugin/ecology", tmp_path / "dump"
    (eco / "critters").mkdir(parents=True)
    d.mkdir()
    (eco / "actors.json").write_text('{"actors":[]}')
    (eco / "critters/cy+001.jsonl").write_text('{"base":"Skyrim.esm:critterSpawnFirefly24x7","fid":"F00002","x":4100.0,"y":10.0,"z":5.0}\n')
    head = "cx\tcy\tfid\tx\ty\tz\trz\tbase\tbase_edid\tsig\n"
    (d / "eco_npcs.tsv").write_text("edid\tkey\tlevel_kind\tlevel\tstats_template\tautocalc\n")
    (d / "ecology.tsv").write_text(head + "1\t0\tF00002\t4100.5\t10\t5\t0\tK\tcritterSpawnFirefly24x7\tActivator\n")
    rep = v.Report()
    v.ecology_rows(rep, tmp_path / "plugin", d)
    assert all(r["result"] == "PASS" for r in rep.rows if "critter" in r["requirement"]), rep.md()
    (d / "ecology.tsv").write_text(head + "1\t0\tF00002\t4100.5\t10\t5\t0\tK\tSomethingElse\tActivator\n"
                                   + "1\t0\tF00003\t4100.5\t10\t5\t0\tK\tcritterSpawnFirefly24x7\tActivator\n")
    rep = v.Report()
    v.ecology_rows(rep, tmp_path / "plugin", d)
    assert sum(r["result"] != "PASS" for r in rep.rows if "critter" in r["requirement"]) == 2, rep.md()


def test_every_npc_of_the_file_is_judged_for_a_player_level_multiplier(tmp_path):
    eco, d = tmp_path / "plugin/ecology", tmp_path / "dump"
    eco.mkdir(parents=True)
    d.mkdir()
    (eco / "actors.json").write_text('{"actors":[]}')
    (d / "ecology.tsv").write_text("cx\tcy\tfid\tx\ty\tz\trz\tbase\tbase_edid\tsig\n")
    (d / "eco_npcs.tsv").write_text("edid\tkey\tlevel_kind\tlevel\tstats_template\tautocalc\nSomeModActor\tK\tpc_mult\t1\tFalse\tFalse\n")
    rep = v.Report()
    v.ecology_rows(rep, tmp_path / "plugin", d)
    bad = [r for r in rep.rows if "no NPC_ of our file" in r["requirement"]]
    assert len(bad) == 1 and bad[0]["result"] == "FAIL" and "SomeModActor" in bad[0]["detail"]


def test_dressing_rows(tmp_path):
    dr = tmp_path / "plugin/dressing"
    rep = v.Report()
    v.dressing_rows(rep, tmp_path / "plugin")
    assert rep.rows[0]["result"] == "PASS"
    dr.mkdir(parents=True)
    (dr / "manifest.json").write_text('{"refs": 12}')
    (dr / "check.json").write_text('{"fault_count": 0, "faults": []}')
    rep = v.Report()
    v.dressing_rows(rep, tmp_path / "plugin")
    assert [r["result"] for r in rep.rows] == ["PASS", "PASS"]
    (dr / "check.json").write_text('{"fault_count": 2, "faults": ["a", "b"]}')
    rep = v.Report()
    v.dressing_rows(rep, tmp_path / "plugin")
    assert rep.rows[-1]["result"] == "FAIL"


def test_flower_grass_thick():
    from tools.newworld import verify as v
    assert v.flower_grass_thick({"ANW_FF_ESpTulipRed": 100, "ANW_FF_ESuPoppy02Red": 40, "ANW_KotM_ALPAGrassFern01": 90}) == ["ANW_FF_ESpTulipRed"]

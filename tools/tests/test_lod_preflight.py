"""The LOD preflight's two halves agree: every step lod.ps1 accepts has code behind it, and lod.sh reads the
machine's preflight output (a recorded sample, as SSH delivers it) into its report and names what it cannot read."""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PS1 = REPO / "infra/gpu-box/lod.ps1"
ESM = "bb1a82f4b295008252bb6eeade5a2ebc7d6aea855390158bf6ea6dd6bf00e818"
LOD = "664b3ada801d43c57a662e5c4a76eef6ab11354fb92f1ac801752eaabe96e5ff"
XLODGEN = "082a2fb77ac528b789535ac74dd23897cbba89e6fc535c806579c3bd45588d91"
DYNDOLOD = "2826037d9efa90815fb793eb8690c416d27596af15a66d68e6123583d93a18c1"
RESOURCES = "562280d83dc14d46c557db6df740d7ee04a83940557eeaf9b0fdac43c86484c5"
RULES = "f8a8bbc71a21123305bcf74e7899472365ba3a2203f626775004fda25530c2bc"
# the play machine's answer to `lod.ps1 -Step preflight -World ArgoniaSmallWorld -Small`, 2026-11-11, CRLF as sent
SAMPLE = "\r\n".join([
    f"[16:12:03] tool xlodgen {XLODGEN}",
    f"[16:12:03] tool dyndolod {DYNDOLOD}",
    f"[16:12:03] tool dyndolod-resources {RESOURCES}",
    "[16:12:04] disk free 47.9 GB",
    "[16:12:04] ram free 12.7 GB",
    f"[16:12:04] have DynDOLOD_SSE_argoniasmallworldesm.ini {RULES}",
    f"[16:12:04] have ArgoniaSmallWorld.esm {ESM}",
    f"[16:12:04] have ArgoniaSmallWorld.lod {LOD}",
    "[16:12:04] worldspaces in the preset at 1: ArgoniaSmallWorld=1",
    "[16:12:04] preset worlds at 1: ArgoniaSmallWorld",
    "[16:12:04] have lodmodels 1",
    "[16:12:04] preflight OK", ""])
WANT = [f"have ArgoniaSmallWorld.esm {ESM}", f"have ArgoniaSmallWorld.lod {LOD}",
        f"have DynDOLOD_SSE_argoniasmallworldesm.ini {RULES}", f"tool xlodgen {XLODGEN}", f"tool dyndolod {DYNDOLOD}",
        f"tool dyndolod-resources {RESOURCES}", "have lodmodels 1"]


def read(tmp_path, text, want=WANT):
    f = tmp_path / "machine.txt"
    f.write_bytes(text.encode())
    p = subprocess.run([str(REPO / "infra/gpu-box/lod.sh"), "read-machine", str(f), *want], capture_output=True, text=True)
    return p.returncode, p.stdout.splitlines()


def test_every_step_the_machine_script_accepts_has_code():
    """A step named in -Step's list with no case in the switch would fall through to "<step> OK" having done nothing."""
    text = PS1.read_text()
    steps = set(re.findall(r"'([a-z]+)'", re.search(r"ValidateSet\(([^)]*)\)\]\[string\]\$Step", text).group(1)))
    body = text[text.index("\nswitch ($Step) {"):]
    cases = set(re.findall(r"^  '([a-z]+)' \{", body, re.M))
    assert steps == cases
    assert re.search(r"^  default \{ throw ", body, re.M)


def test_the_machines_report_is_read_whole(tmp_path):
    rc, lines = read(tmp_path, SAMPLE)
    assert rc == 0
    assert lines == ["disk free 47.9 GB", "ram free 12.7 GB", "preset worlds at 1: ArgoniaSmallWorld", "have lodmodels 1"]


def test_an_empty_answer_is_one_fault_that_says_so(tmp_path):
    for text in ("", "\r\n"):
        rc, lines = read(tmp_path, text)
        assert rc == 1 and len(lines) == 1 and "printed nothing" in lines[0]


def test_an_answer_with_no_report_is_one_fault_that_quotes_it(tmp_path):
    """The step that ran no check and still said OK: named as that, never as three tools off their hashes."""
    rc, lines = read(tmp_path, "[15:58:40] preflight OK\r\n")
    assert rc == 1 and len(lines) == 1
    assert "ran none of its checks" in lines[0] and '"preflight OK"' in lines[0] and "pinned hash" not in lines[0]


def test_each_missing_or_different_line_is_named_with_what_the_machine_said(tmp_path):
    other = "0" * 64
    text = SAMPLE.replace(f"tool dyndolod {DYNDOLOD}", f"tool dyndolod {other}").replace("have lodmodels 1", "have lodmodels 0")
    text = text.replace(f"[16:12:04] have ArgoniaSmallWorld.lod {LOD}\r\n", "").replace("[16:12:04] ram free 12.7 GB\r\n", "")
    rc, lines = read(tmp_path, text)
    faults = [x for x in lines if x.startswith("FAULT ")]
    assert rc == 1 and len(faults) == 4
    assert 'FAULT the machine\'s preflight printed no "ram free" line' in faults
    assert f"FAULT tool dyndolod on the machine is not at its pinned hash {DYNDOLOD[:12]} (the machine printed: tool dyndolod {other})" in faults
    assert f'FAULT the machine\'s ArgoniaSmallWorld.lod is not the one built here, {LOD} (the machine printed: no "have ArgoniaSmallWorld.lod" line)' in faults
    assert "FAULT the machine does not hold the 1 LOD models built here (the machine printed: have lodmodels 0)" in faults


def test_the_machines_own_faults_and_an_unfinished_run_fail(tmp_path):
    rc, lines = read(tmp_path, SAMPLE.replace("[16:12:04] preflight OK", "[16:12:04] FAULT machine: still running SkyrimSE\r\npreflight: 1 faults"))
    assert rc == 1 and [x for x in lines if x.startswith("FAULT ")] == ["FAULT machine: still running SkyrimSE"]
    rc, lines = read(tmp_path, SAMPLE.replace("[16:12:04] preflight OK\r\n", "Connection to 10.0.0.1 closed by remote host.\r\n"))
    assert rc == 1 and "did not finish" in lines[-1] and "closed by remote host" in lines[-1]

"""L1: every package target is a persistent reference (place_build.check_package_targets)."""
import pytest

from tools.argonia_world.place_build import check_package_targets

BED = "8933BE:King of the Murkmire.esp"


def _recs(persistent):
    return [{"type": "PACK", "edid": "ARG_Npc_T_Sleep", "location": {"ref": BED}},
            {"type": "CELL", "refs": [{"formKey": BED, "persistent": persistent}]}]


def test_persistent_target_passes():
    check_package_targets(_recs(True))


def test_temporary_or_missing_target_fails():  # the failure it was added for, proven on purpose
    with pytest.raises(ValueError, match="not persistent"):
        check_package_targets(_recs(False))
    with pytest.raises(ValueError, match="not persistent"):
        check_package_targets(_recs(True)[:1])


HOME = "893374:King of the Murkmire.esp"
NPC = "000886:Argonia.esm"


def _home(owner):
    return [{"type": "PACK", "edid": "ARG_Npc_T_Sleep", "formKey": "000885:Argonia.esm", "location": {"cell": HOME, "radius": 0}},
            {"type": "NPC_", "formKey": NPC, "packages": ["000885:Argonia.esm"]},
            {"type": "CELL", "formKey": HOME, "refs": [{"formKey": BED, "persistent": True, "owner": owner}]}]


def test_sleep_in_home_cell_with_own_bed_passes():  # the native sleep (game-10): in cell, the template finds her bed
    check_package_targets(_home(NPC))


def test_home_cell_without_the_sleepers_bed_fails():
    with pytest.raises(ValueError, match="no ref there owned by"):
        check_package_targets(_home("000999:Argonia.esm"))
    with pytest.raises(ValueError, match="not a cell of these records"):
        check_package_targets(_home(NPC)[:2])

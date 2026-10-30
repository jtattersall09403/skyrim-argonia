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

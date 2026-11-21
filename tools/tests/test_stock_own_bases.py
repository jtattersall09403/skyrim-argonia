from tools.places.own_bases import SAP_POOL
from tools.places.stock.plan import plugins_of


def test_own_bases_pseudo_plugin_is_never_read_as_a_file():
    names = plugins_of([SAP_POOL, "Skyrim.esm:000001", "King of the Murkmire.esp:0000AA"])
    assert "ArgoniaOwn.esp" not in names and "King of the Murkmire.esp" in names

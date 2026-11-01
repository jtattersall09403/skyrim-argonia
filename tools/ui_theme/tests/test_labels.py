

def test_skyui_table_written_at_its_own_path(tmp_path):
    from tools.ui_theme import labels
    raw = b"\xff\xfe" + "$MOD CONFIGURATION\tMOD CONFIGURATION\r\n$SKI_INFO6\tEach group.\r\n".encode("utf-16-le")
    n = labels.write_table(raw, tmp_path, labels.SKYUI_TABLE)
    text = (tmp_path / labels.SKYUI_TABLE).read_bytes().decode("utf-16")
    assert n == 1 and "$MOD CONFIGURATION\tMod configuration\r\n" in text and "Each group." in text

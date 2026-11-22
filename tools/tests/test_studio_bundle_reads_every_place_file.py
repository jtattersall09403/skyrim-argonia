"""The studio page reads every place file a draft bundle carries: its loader once left out paint.jsonl, so committed
ground paint was never drawn (only a session's own strokes were)."""
import re
from pathlib import Path

from tools.places import draft_bundle

JS = Path(__file__).resolve().parents[1] / "places" / "studio" / "web" / "js" / "bundle.js"


def test_the_page_loads_every_file_of_a_draft_bundle():
    src = JS.read_text()
    m = re.search(r"Promise\.all\(\[([^\]]*)\]\s*\.map\(\(f\) => getJsonl\(`\$\{at\}\$\{f\}\.jsonl`", src)
    assert m, "the loader's list of place files was not found"
    loaded = set(re.findall(r"'(\w+)'", m.group(1)))
    assert set(draft_bundle.FILES) <= loaded, set(draft_bundle.FILES) - loaded

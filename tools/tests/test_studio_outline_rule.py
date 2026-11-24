"""The selection's outline is drawn round its outer edge only (objects.js outlineOf): each piece's mesh again as back
faces pushed out along their normals, never lines over its surfaces. The page needs three.js and a GPU to draw it, so
the rule is held here on the source, and its look on a real place by the capture the place-look recipe takes."""
import re
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "places/studio/web/js/objects.js").read_text()


def test_the_outline_is_a_back_face_rim_and_no_line_drawing():
    body = SRC[SRC.index("  outlineOf(refs) {"):SRC.index("  worldBox(ref) {")]
    assert "THREE.BackSide" in body and "normalMatrix * normal" in body, "a rim pushed out along the normals"
    assert not re.search(r"EdgesGeometry|LineSegments|WireframeGeometry|wireframe", body), "no lines over the surfaces"

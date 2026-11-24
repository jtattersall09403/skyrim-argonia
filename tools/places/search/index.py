"""The vector index over the catalogue, on disk in out/places/search/ (derived, never committed).

  vectors.npy    float16 [N, 384], unit rows, in the order of rows.jsonl
  rows.jsonl     {key, h, edid, name, model, type, kind, nordic, plugin}: h is the hash of the text embedded

`update` re-embeds only the keys whose text changed and drops keys no longer in the catalogue. `query` scores
cosine similarity plus lexical boosts: an editor id or name equal to the query (spaces and case ignored) always
ranks first, a prefix next, then a share of the query's words found in the base's words; to that it adds the look score, the
CLIP similarity of the query to the model's thumbnail (look.py), on the query's own scale and weighted by LOOK_WEIGHT,
and says per hit which half matched: name (exact or prefix), text, look or both."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TYPE_WORDS = {
    "STAT": "static", "MSTT": "moving static", "DOOR": "door", "CONT": "container chest", "FURN": "furniture",
    "LIGH": "light", "ACTI": "activator", "TREE": "tree", "FLOR": "plant flora", "GRAS": "grass ground cover",
    "MISC": "clutter item", "SCRL": "scroll", "BOOK": "book", "INGR": "ingredient", "WEAP": "weapon",
    "ARMO": "armor", "ALCH": "potion food", "KEYM": "key", "IDLM": "idle marker", "TXST": "decal",
}
TYPE_KIND = {"STAT": "static", "MSTT": "static", "DOOR": "door", "CONT": "container", "FURN": "furniture",
             "LIGH": "light", "ACTI": "activator", "TREE": "tree", "FLOR": "plant", "GRAS": "groundcover",
             "MISC": "clutter", "BOOK": "clutter", "INGR": "clutter", "WEAP": "clutter", "ARMO": "clutter",
             "ALCH": "clutter", "KEYM": "clutter", "SCRL": "clutter", "IDLM": "marker", "NPC_": "actor"}
# Modders' words for things, glossed in plain English so a plain query finds them (applied to the base's words).
GLOSS = {"boardwalk": "wooden walkway", "walkway": "boardwalk", "pier": "wooden walkway jetty", "dock": "jetty pier",
         "plank": "wooden board", "brazier": "fire bowl", "sconce": "wall light", "bedroll": "bed sleeping",
         "xanmeer": "ziggurat ruin", "hist": "sacred tree", "palisade": "wooden wall fence", "cot": "bed",
         "stilt": "raised on posts", "lamp": "light", "clutter": "small item", "hay": "straw"}
# The look score of a hit is its CLIP cosine placed on the query's own scale: 0 at the median thumbnail, 1 at the
# 99.9th percentile (CLIP cosines bunch in a narrow band whose level differs by query); it adds LOOK_WEIGHT * z**2.
LOOK_WEIGHT = 0.2
LOOK_TEMPLATES = ("a 3d render of {}.", "a photo of {}.", "{}", "a 3d model of {}, a video game prop.")
WORD_BOOST = 0.15   # times the share of the query's words (plurals folded) found in the base's words
TEXT_FLOOR = 0.6    # a typical bge cosine of a query to an unrelated row
ROW_FIELDS = ("key", "edid", "name", "model", "type", "kind", "nordic", "plugin")


def out_dir() -> Path:
    return Path(os.environ.get("PLACES_OUT", ROOT / "out" / "places"))


def catalogue_path(p: str | None = None) -> Path:
    return Path(p) if p else out_dir() / "catalogue" / "bases.jsonl"


def words(s: str | None) -> list[str]:
    """Editor ids and model paths into words: camel case, digits and separators split, lower case."""
    if not s:
        return []
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [w for w in re.split(r"[^a-z]+", s.lower()) if len(w) > 1]


def base_kind(b: dict) -> str:
    return b.get("kind") or TYPE_KIND.get(b.get("type", ""), "other")


def base_text(b: dict) -> str:
    """What is embedded: the catalogue's plain-English descriptor (`text`) with a gloss of modders' words; a base
    without one (a bundle's bases) gets the same built from its own fields."""
    model = (b.get("model") or "").rsplit(".", 1)[0]
    found = set(words(b.get("edid"))) | set(words(b.get("name"))) | set(words(model.split("/")[-1]))
    gloss = ", ".join(sorted({g for w in found for k, g in GLOSS.items() if k in w}))
    if b.get("text"):
        return ". ".join(p for p in (gloss, b["text"]) if p)
    parts = [gloss, b.get("name") or "", " ".join(words(b.get("edid"))), TYPE_WORDS.get(b.get("type", ""), ""),
             " ".join(words(model.replace("/", " "))), " ".join(words(" ".join(b.get("keywords") or [])))]
    return ". ".join(p for p in parts if p)


def stem(w: str) -> str:
    """Plurals folded, so "cattails" is "cattail"."""
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def squash(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def read_jsonl(p: Path):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


class Index:
    _open: dict[str, Index] = {}
    _lock = threading.Lock()

    def __init__(self, d: Path) -> None:
        self.dir = d
        self.rows: list[dict] = []
        self.vec = np.zeros((0, 384), np.float32)
        self.embedder = None
        self._source_keys: dict[str, tuple[float, set]] = {}
        self._mtime = None
        self._state: tuple = ([], self.vec, [], [], [])
        self.clip = None
        self._look: tuple = (None, None, None)   # (mtime, row -> look vector index or -1, vectors)
        self._status: tuple = (None, {})
        self.load()

    @classmethod
    def open(cls, d: Path | None = None) -> Index:
        d = d or out_dir() / "search"
        with cls._lock:
            if str(d) not in cls._open:
                cls._open[str(d)] = cls(d)
            ix = cls._open[str(d)]
        ix.reload_if_changed()
        return ix

    def load(self) -> None:
        """Read the index from disk. Everything a query reads is one tuple (`_state`), swapped in whole, so a query
        on another thread sees the old index or the new one, never rows of one against vectors of the other."""
        rp, vp = self.dir / "rows.jsonl", self.dir / "vectors.npy"
        rows, vec, mtime = self.rows, self.vec, self._mtime
        if rp.exists() and vp.exists():
            mtime = vp.stat().st_mtime
            rows = list(read_jsonl(rp))
            vec = np.load(vp).astype(np.float32)
            if len(rows) != len(vec):   # caught between the two files of an update: keep what is loaded
                return
        edid = [squash(r.get("edid")) for r in rows]
        name = [squash(r.get("name")) for r in rows]
        wordset = [{stem(w) for w in words(r.get("edid")) + words(r.get("name")) +
                    words((r.get("model") or "").replace("/", " "))} for r in rows]
        self._state = (rows, vec, edid, name, wordset)
        self.rows, self.vec, self.edid, self.name, self.wordset = self._state
        self._mtime = mtime

    def reload_if_changed(self) -> None:
        vp = self.dir / "vectors.npy"
        if vp.exists() and vp.stat().st_mtime != self._mtime:
            with self._lock:
                if vp.stat().st_mtime != self._mtime:
                    self.load()

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.embedder is None:
            from tools.places.search.embed import Embedder
            self.embedder = Embedder()
        return self.embedder(texts)

    def look_state(self):
        """Each row's index into the look vectors (-1 when its model has none), reloaded when the vectors change."""
        from tools.places.search import look
        vp = look.look_dir() / "vectors.npy"
        m = vp.stat().st_mtime if vp.exists() else None
        rows = self._state[0]
        if self._look[0] != m or self._look[1] is None or len(self._look[1]) != len(rows):
            keys, v = look.load_vectors()
            at = {k: i for i, k in enumerate(keys)}
            ix = np.fromiter((at.get(look.model_key(r["model"]), -1) if r.get("model") else -1 for r in rows),
                             np.int64, len(rows))
            self._look = (m, ix, v.astype(np.float32))
        return self._look[1], self._look[2]

    def look_status(self) -> dict:
        from tools.places.search import look
        sp = look.look_dir() / "status.jsonl"
        m = sp.stat().st_mtime if sp.exists() else None
        if self._status[0] != m:
            self._status = (m, look.status())
        return self._status[1]

    def embed_look(self, q: str) -> np.ndarray:
        if self.clip is None:
            from tools.places.search.clip import Clip
            self.clip = Clip()
        e = self.clip.text([t.format(q) for t in LOOK_TEMPLATES]).mean(0)
        return e / np.linalg.norm(e)

    def update(self, catalogue: Path) -> dict:
        """Bring the index level with the catalogue, embedding only new or changed keys; atomic on disk."""
        old = {r["key"]: (r, self.vec[i]) for i, r in enumerate(self.rows)}
        rows, vecs, todo = [], [], []
        for b in read_jsonl(catalogue):
            text = base_text(b)
            h = hashlib.sha1(text.encode()).hexdigest()[:16]
            row = {k: b.get(k) for k in ROW_FIELDS} | {"kind": base_kind(b), "nordic": bool(b.get("nordic")), "h": h}
            prev = old.get(b["key"])
            if prev and prev[0].get("h") == h:
                vecs.append(prev[1])
            else:
                vecs.append(None)
                todo.append((len(rows), text))
            rows.append(row)
        if todo:
            new = self.embed([t for _, t in todo])
            for (i, _), v in zip(todo, new):
                vecs[i] = v
        mat = np.stack(vecs).astype(np.float16) if vecs else np.zeros((0, 384), np.float16)
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp_r, tmp_v = self.dir / "rows.jsonl.tmp", self.dir / "vectors.tmp.npy"
        tmp_r.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        np.save(tmp_v, mat)
        tmp_r.replace(self.dir / "rows.jsonl")
        tmp_v.replace(self.dir / "vectors.npy")
        self.load()
        return {"rows": len(rows), "embedded": len(todo), "dropped": len(set(old) - {r["key"] for r in rows})}

    def source_keys(self, source_id: str) -> set:
        p = out_dir() / "bundles" / f"src.{source_id}" / "bases.jsonl"
        if not p.exists():
            return set()
        m = p.stat().st_mtime
        hit = self._source_keys.get(source_id)
        if not hit or hit[0] != m:
            hit = (m, {b["key"] for b in read_jsonl(p)})
            self._source_keys[source_id] = hit
        return hit[1]

    def query(self, q: str, scope: str = "all", source_id: str | None = None, kind: str | None = None,
              limit: int = 40) -> list[dict]:
        q = (q or "").strip()
        rows, vec, edids, names, wordsets = self._state
        n = len(rows)
        if not n:
            return []
        mask = np.ones(n, bool)
        if scope == "source":
            keys = self.source_keys(source_id or "")
            mask &= np.fromiter((r["key"] in keys for r in rows), bool, n)
        if kind:
            kinds = set(kind.split(","))
            mask &= np.fromiter((r.get("kind") in kinds for r in rows), bool, n)
        name = np.zeros(n, bool)
        text = np.zeros(n, np.float32)
        lookv = np.zeros(n, np.float32)
        lookz = np.zeros(n, np.float32)
        if not q:
            score = np.zeros(n, np.float32)
        else:
            text = vec @ self.embed([q])[0]
            score = text.copy()
            sq, qw = squash(q), {stem(w) for w in words(q)}
            for i in np.flatnonzero(mask):
                e, nm = edids[i], names[i]
                if sq and (sq == e or sq == nm):
                    score[i] += 10.0
                    name[i] = True
                elif sq and (e.startswith(sq) or nm.startswith(sq)):
                    score[i] += 5.0
                    name[i] = True
                elif qw:
                    score[i] += WORD_BOOST * len(qw & wordsets[i]) / len(qw)
            li, lv = self.look_state()
            if len(lv):
                has = li >= 0
                lookv[has] = lv[li[has]] @ self.embed_look(q)
                p50, p999 = np.percentile(lookv[has], [50, 99.9])
                lookz[has] = np.maximum((lookv[has] - p50) / max(p999 - p50, 1e-6), 0)
                score += LOOK_WEIGHT * lookz ** 2
        score = np.where(mask, score, -np.inf)
        k = min(limit, int(mask.sum()))
        if k <= 0:
            return []
        top = np.argpartition(-score, k - 1)[:k]
        top = top[np.argsort(-score[top])]
        from tools.places.search import look
        st = self.look_status() if q else {}
        out = []
        for i in top:
            t_part = float(text[i]) - TEXT_FLOOR
            l_part = LOOK_WEIGHT * float(lookz[i]) ** 2
            matched = ("name" if name[i] else "both" if t_part > 0.1 and l_part > 0.1 else
                       "look" if l_part > t_part else "text")
            h = {k2: v for k2, v in rows[i].items() if k2 != "h"} | {
                "score": round(float(score[i]), 4), "text_score": round(float(text[i]), 4),
                "look_score": round(float(lookv[i]), 4), "look_z": round(float(lookz[i]), 3), "matched": matched}
            if rows[i].get("model"):
                k = look.model_key(rows[i]["model"])
                p = look.thumb_path(k)
                r = st.get(k)
                h["look"] = str(p) if p.exists() else None
                h["look_why"] = None if r is None else r.get("why")
            out.append(h)
        return out

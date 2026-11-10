"""The vector index over the catalogue, on disk in out/places/search/ (derived, never committed).

  vectors.npy    float16 [N, 384], unit rows, in the order of rows.jsonl
  rows.jsonl     {key, h, edid, name, model, type, kind, nordic, plugin}: h is the hash of the text embedded

`update` re-embeds only the keys whose text changed and drops keys no longer in the catalogue. `query` scores
cosine similarity plus lexical boosts: an editor id or name equal to the query (spaces and case ignored) always
ranks first, a prefix next, then every query word found in the base's words."""
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
        wordset = [set(words(r.get("edid"))) | set(words(r.get("name"))) |
                   set(words((r.get("model") or "").replace("/", " "))) for r in rows]
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
        if not q:
            score = np.zeros(n, np.float32)
        else:
            score = vec @ self.embed([q])[0]
            sq, qw = squash(q), set(words(q))
            for i in np.flatnonzero(mask):
                e, nm = edids[i], names[i]
                if sq and (sq == e or sq == nm):
                    score[i] += 2.0
                elif sq and (e.startswith(sq) or nm.startswith(sq)):
                    score[i] += 1.0
                elif qw and qw <= wordsets[i]:
                    score[i] += 0.15
        score = np.where(mask, score, -np.inf)
        k = min(limit, int(mask.sum()))
        if k <= 0:
            return []
        top = np.argpartition(-score, k - 1)[:k]
        top = top[np.argsort(-score[top])]
        return [{k2: v for k2, v in rows[i].items() if k2 != "h"} | {"score": round(float(score[i]), 4)}
                for i in top]

"""The promise gate (ported from the old repo's worldgen/promise_gate.py and
promise_classes.py, decision 0104 decision 5): every row of a place's promise
ledger is filled by a placed thing, or excused with one of the three reasons.

Ported whole for the rules the integrity check reads. Not ported (they read
build outputs this repo does not hold): the published-bundle route index, the
facts gate and the CLI. The shell-class and service-size rules read the kit
manifests (`apps/world-studio/public/kits`); with no manifests they judge
nothing, exactly as the old gate did for a filler with no resolvable shell.
"""
from __future__ import annotations

import hashlib
import json
import re

LEDGER_SCHEMA_VERSION = 1
PROMISE_KINDS = ("service", "occupant", "operator", "provision", "socketBucket", "safeInterior",
                 "interior", "entrance", "underwaterAccess", "travelStation", "prose", "quest")
#: kinds kept by the builder's confirmation, not by a placed thing: the row's
#: text is re-read against the built place and `confirmed: {sha, note}` pins
#: it (sha = blueprint_promises.text_sha of the text); an untrue line is fixed
#: by editing its source record (0104 decision 6), never left unconfirmed
CONFIRMED_KINDS = ("prose", "quest")
#: the only three reasons a promise may stay unfilled (decision 0102 decision
#: 3; owner ruling 2026-10-04, R113: a missing asset is never one, the record
#: is rewritten or the spot redesigned)
UNFILLED_REASONS = ("later-phase-system", "gpu-judgement", "owner-world-call")
#: blueprint collections whose rows may carry `fills`
FILLING_COLLECTIONS = ("parcels", "doors", "questSockets")
#: the physical nouns a record's prose can promise (audit10: bones, steps,
#: signs, a shed and a seep were promised and never built, and every gate was
#: green): noun -> (the prose pattern, the asset/id words that show it). Each
#: noun a `prose` row names is a `provision` row `thing-<noun>` that a placed
#: thing fills (blueprint_promises.claim_rows); `record_coherence` reads the
#: same table against the compiled bundle. Bare words that are also ordinary
#: prose are read only as the noun: "as well" and "well organised" are no well, "in the spring" is
#: the season, "takes its toll" no toll, "stable ground" no stable.
PHYSICAL_NOUNS: dict[str, tuple[str, tuple[str, ...]]] = {
    "boat": (r"\b(?:boats?|canoes?|rafts?|skiffs?)\b", ("boat", "canoe", "raft", "skiff", "ship")),
    "ferry": (r"\bferry\b|\bferries\b", ("ferry",)),
    "sign": (r"\b(?:signs?|signposts?|signboards?|signage)\b(?!\s+of\b)", ("sign",)),
    "steps": (r"(?<!\bman )(?<!\bwoman )(?<!\bhe )(?<!\bshe )(?<!\bwho )(?<!\bone )"
              r"(?<!\bsomeone )\bsteps\b(?!\s+(?:down|up|out|in|back|over|across|aside|off)\b)"
              r"|\b(?:stairs?|stairways?)\b", ("step", "stair")),
    "plank crossing": (r"\bplanks?\b|\bboardwalks?\b",
                       ("plank", "dock", "boardwalk", "walkway", "bridge", "timber")),
    "well": (r"(?<!\bas )\bwells?\b(?![-,])"
             r"(?!\s+(?:kept|before|after|known|over|into|above|below|enough|off|made|built|\w+ed))",
             ("well",)),
    "spring": (r"(?<!\bin )(?<!\bin the )(?<!\bthis )(?<!\blast )(?<!\bnext )(?<!\bthat )"
               r"(?<!\bevery )(?<!\beach )(?<!\bby )(?<!\buntil )(?<!\bsince )(?<!\bthe late )"
               r"(?<!\bthe early )\bsprings?\b"
               r"(?!\s+(?:rains?|floods?|thaw|seasons?|tides?|planting|and\s+summer|or\s+summer))",
               ("spring",)),
    "tarn": (r"\btarns?\b", ("tarn", "pond", "pool")),
    "seep": (r"\bseeps?\b", ("seep",)),
    "shed": (r"\bsheds?\b", ("shed",)),
    "ore": (r"\bores?\b", ("ore", "ingot", "bloom")),
    "bones": (r"\bbones?\b|\bskulls?\b", ("bone", "skull", "spine")),
    "farmhouse": (r"\bfarmhouses?\b", ("farmhouse",)),
    "lantern": (r"\blanterns?\b|\blamps?\b", ("lantern", "lamp")),
    "fire": (r"\bfires?\b|\bhearths?\b|\bbraziers?\b|\bfire[- ]?pits?\b",
             ("fire", "brazier", "hearth", "campfire", "firepit")),
    "channel": (r"\bchannels?\b", ("channel", "canal")),
    "canal": (r"\bcanals?\b", ("canal", "channel")),
    # "a Hist a day upriver" stands elsewhere, not at the place
    "Hist tree": (r"\bHist\b(?!\s+(?:a|an|one|two|three|half a)\s+(?:days?|hours?|miles?)\b)",
                  ("hist",)),
    "toll": (r"(?<!\btakes its )(?<!\btook its )(?<!\btake its )(?<!\btaken its )"
             r"(?<!\btakes their )(?<!\btook their )(?<!\btake a )\btolls?\b"
             r"(?!\s+(?:company|companies|men|officers?)\b)", ("toll",)),
    "bridge": (r"\bbridges?\b", ("bridge",)),
    "dock": (r"\bdocks?\b|\bjett(?:y|ies)\b|\bpiers?\b|\bquays?\b",
             ("dock", "jetty", "pier", "quay", "landing", "stage")),
    "shrine": (r"\bshrines?\b", ("shrine",)),
    "mine": (r"\bmines?\b(?!\s+(?:is|was))", ("mine", "diggings")),
    "tower": (r"\btowers?\b", ("tower",)),
}


def physical_nouns(text: str) -> list[str]:
    """The PHYSICAL_NOUNS a text names (sorted); "Hist" is matched case-sensitively."""
    return sorted(n for n, (pat, _) in PHYSICAL_NOUNS.items()
                  if re.search(pat, str(text or ""), 0 if n == "Hist tree" else re.I))


#: nouns a placed thing cannot show: water courses (the hydrology holds them)
#: and a toll (a relation); record_coherence still checks them
NOT_PLACED = ("channel", "canal", "toll")


#: a negation governs the nouns after it up to the end of its clause
_NEGATION = re.compile(r"\b(?:no|never|without|nor|neither|not (?:an?|the|any|even))\b", re.I)
_CLAUSE_END = re.compile(r"[.;:!?,—–]|\bbut\b|\band\b(?=\s+(?:an?|the|its|their|one|two|three)\b)", re.I)


def _named_unnegated(noun: str, text: str) -> bool:
    pat = PHYSICAL_NOUNS[noun][0]
    return any(not _NEGATION.search(_CLAUSE_END.split(text[:m.start()])[-1])
               for m in re.finditer(pat, text, 0 if noun == "Hist tree" else re.I))


def thing_nouns(text: str) -> list[str]:
    """The physical nouns of a text that a placed thing must show; a noun a
    negation governs in its clause ("no wall and no tower") is not promised."""
    text = str(text or "")
    return [n for n in physical_nouns(text) if n not in NOT_PLACED and _named_unnegated(n, text)]


def noun_slug(noun: str) -> str:
    return noun.lower().replace(" ", "-")


#: noun -> the other nouns whose filled `thing-` row also shows it (a plank
#: run over a crossing is the bridge a record names, and the reverse)
SHOWN_BY: dict[str, tuple[str, ...]] = {"bridge": ("plank crossing",),
                                        "plank crossing": ("bridge",)}
#: the bundle key that holds the placements of the route bundles at a place
ROUTE_KEY = "routePlacements"


def bundle_ids(bundle: dict | None) -> set[str] | None:
    """Every id the published bundle carries (placements, compiled objects,
    doors, sockets, pools), or None when no bundle is given (the compile stage)."""
    if bundle is None:
        return None
    st = bundle.get("settlement") or {}
    rows = [r for key in ("placements", "compiledObjects", "doors", "sockets", "pools", ROUTE_KEY)
            for src in (bundle, st) for r in src.get(key) or []]
    return ({str(r["id"]) for r in rows if isinstance(r, dict) and r.get("id")}
            | {str(i) for key in ("placementIds", "compiledObjectIds") for i in st.get(key) or []})


def _in_bundle(oid: str, ids: set[str]) -> bool:
    """A layout id is in the bundle as itself, or as the tail or a segment of
    a compiled id (`<place>.parcel.<p>.assembly.<op id>`)."""
    return oid in ids or any(i.endswith("." + oid) or f".{oid}." in i for i in ids)


def with_layout_aliases(ids: set[str] | None, layout: dict | None) -> set[str] | None:
    """`ids` plus the layout uid of every parcel whose bound id is in the
    bundle: a parcel's building compiles under the parcel id
    (`<place>.parcel.<p>.<parcel>.building`), so a builder cites the layout
    uid and the gate maps it (a layout `bind` op, kind ``parcel``). A run
    piece (kind ``run``, 0-based ``index``) compiles as
    `<place>.parcel.<run>.piece.<index + 1>`, so its uid maps the same way."""
    if ids is None or not layout:
        return ids
    aliases: set[str] = set()
    for op in layout.get("ops") or []:
        if not (isinstance(op, dict) and op.get("op") == "bind" and op.get("uid") and op.get("id")):
            continue
        if op.get("kind") == "parcel" and _in_bundle(str(op["id"]), ids):
            aliases.add(str(op["uid"]))
        elif op.get("kind") == "run" and isinstance(op.get("index"), int):
            piece = f"{op['id']}.piece.{op['index'] + 1}"
            if any(i.endswith("." + piece) for i in ids):
                aliases.add(str(op["uid"]))
    return ids | aliases


def layout_sockets(layout: dict | None) -> list[dict]:
    """The authored socket ops of a layout (the home table of placed
    interactables, 0104 decision 4)."""
    if not layout:
        return []
    return list(layout.get("sockets") or []) + [
        op for op in layout.get("ops") or [] if op.get("op") == "socket"]


def fills_index(bp: dict, sockets: list[dict] | None = None,
                layout: dict | None = None, ledger: dict | None = None) -> dict[str, list[str]]:
    """promise id -> the ids of the sockets, doors, parcels and layout
    placements (any layout op with an `id` or `uid`) that name it in
    ``fills``, and the ids a ledger row names in ``filledBy`` (each filler
    once, sorted). With no ``layout`` or ``ledger`` given, the place's
    committed ``<slug>.layout.json`` and ledger are read, so the compile's
    ``promiseFills`` carries every filler of a row."""
    out: dict[str, set[str]] = {}
    rows = [r for key in FILLING_COLLECTIONS for r in bp.get(key) or [] if isinstance(r, dict)]
    rows += [s for s in sockets or [] if isinstance(s, dict)]
    # a layout op is named by `id`, a `place` op by `uid`
    rows += [op for op in (layout or {}).get("ops") or []
             if isinstance(op, dict) and (op.get("id") or op.get("uid")) and op.get("fills")]
    for row in rows:
        for pid in row.get("fills") or []:
            out.setdefault(pid, set()).add(str(row.get("id") or row.get("uid")))
    # a ledger row may name its fillers by id (`filledBy`): placed things the
    # layout cannot carry `fills` on (a route bundle's stair, a compiled run)
    for row in (ledger or {}).get("promises") or []:
        for fid in row.get("filledBy") or []:
            out.setdefault(row["id"], set()).add(str(fid))
    return {pid: sorted(ids) for pid, ids in sorted(out.items())}


def promise_gate_errors(bp: dict, ledger: dict | None,
                        sockets: list[dict] | None = None, layout: dict | None = None,
                        bundle: dict | None = None) -> list[str]:
    """Every ledger row filled by at least one ``fills`` reference, or
    carrying ``unfilled`` with a valid reason; every ``fills`` id a row of
    this ledger; every physical noun a prose row names has its
    ``thing-<noun>`` row; a prose row naming a physical noun is confirmed
    with the ``ids`` of the placements it rests on. Given the published
    ``bundle``, every filler and confirmation id must be in it. Each message
    is led by its rule id, ``promises.*``."""
    if ledger is None:
        return []
    out: list[str] = []
    ids = with_layout_aliases(bundle_ids(bundle), layout)
    if ledger.get("placeId") != bp.get("id"):
        out.append(f"promises.ledger: ledger placeId {ledger.get('placeId')!r} is not "
                   f"blueprint {bp.get('id')!r}")
    rows = {r["id"]: r for r in ledger.get("promises") or []}
    filled = fills_index(bp, sockets, layout, ledger)
    slug = str(ledger.get("placeId") or "").rsplit(".", 1)[-1]
    named: dict[str, list[str]] = {}
    for pid, row in sorted(rows.items()):
        for noun in thing_nouns(row.get("text")) if row.get("kind") == "prose" else []:
            named.setdefault(noun, []).append(pid)
    out += [f"promises.thing: {', '.join(pids)} name{'s' if len(pids) == 1 else ''} a {noun} and "
            f"the ledger has no row promise.{slug}.thing-{noun_slug(noun)}; regenerate it with "
            f"`blueprint_promises --id {ledger.get('placeId')} --write`"
            for noun, pids in sorted(named.items())
            if f"promise.{slug}.thing-{noun_slug(noun)}" not in rows]
    for pid, fillers in sorted(filled.items()) if ids is not None else []:
        out += [f"promises.built: {f} fills {pid} and is not in the published bundle; fill "
                f"from a placed thing and publish the place" for f in fillers if not _in_bundle(f, ids)]
    for pid, fillers in filled.items():
        if pid not in rows:
            out.append(f"promises.unknown: {', '.join(fillers)} fills {pid!r}, which is no row "
                       f"of {ledger.get('placeId')}'s ledger (regenerate it with "
                       f"`blueprint_promises --id {ledger.get('placeId')} --write`)")
    for pid, row in sorted(rows.items()):
        if row.get("kind") in CONFIRMED_KINDS:
            out += _confirmation_errors(pid, row, ids)
            continue
        unfilled = row.get("unfilled")
        if unfilled is not None:
            reason = (unfilled or {}).get("reason")
            if reason not in UNFILLED_REASONS:
                out.append(f"promises.reason: {pid} is unfilled with reason {reason!r}; the "
                           f"reason is one of {list(UNFILLED_REASONS)} (decision 0102)")
            elif not str((unfilled or {}).get("note") or "").strip():
                out.append(f"promises.reason: {pid} is unfilled ({reason}) with no note")
            if pid in filled:
                out.append(f"promises.both: {pid} is filled by {', '.join(filled[pid])} and "
                           f"also marked unfilled; drop the `unfilled` block")
            continue
        if pid not in filled:
            out.append(f"promises.unfilled: {pid} ({row.get('kind')}: {row.get('text')}) is "
                       f"filled by no socket, door or parcel; add `fills: [\"{pid}\"]` to the "
                       f"thing that keeps it, or give the row `unfilled` with a decision 0102 "
                       f"reason")
    # a promised noun is a class with a minimum (promise_classes)
    return (out + class_errors(rows, filled, bp, layout) + service_errors(rows, filled, bp, layout)
            + thing_errors(rows, filled, bp, layout, bundle))


def _confirmation_errors(pid: str, row: dict, ids: set[str] | None = None) -> list[str]:
    """A prose or quest row: confirmed against its current text, with a note;
    a prose row that names a physical noun also names, in ``confirmed.ids``,
    the placement(s) it rests on, each in the published bundle when one is
    given (a builder's pin alone kept a shed nobody built, audit10)."""
    conf = row.get("confirmed") or {}
    sha = text_sha(row.get("text"))
    if conf.get("sha") != sha:
        return [f"promises.confirm: {pid} ({row.get('kind')}: {str(row.get('text'))[:90]}) is not "
                f"confirmed against the built place{' (its text changed)' if conf else ''}: re-read "
                f"it, edit the source record where the place contradicts it (place skill § Publish, record coherence), "
                f"then set `confirmed: {{\"sha\": \"{sha}\", \"note\": <what in the place keeps it>}}`"]
    if not str(conf.get("note") or "").strip():
        return [f"promises.confirm: {pid} is confirmed with no note naming what keeps it"]
    nouns = thing_nouns(row.get("text")) if row.get("kind") == "prose" else []
    shown = [str(i) for i in conf.get("ids") or []]
    if nouns and not shown:
        return [f"promises.confirm: {pid} names {', '.join(nouns)} and its confirmation names no "
                f"placement: add `ids: [<placement id>, ...]` to `confirmed`"]
    return [f"promises.built: {pid} rests on {i}, which is not in the published bundle"
            for i in shown if ids is not None and not _in_bundle(i, ids)]




def text_sha(text: str) -> str:
    """The pin a `confirmed` block carries: the first 12 hex of the text's sha256."""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:12]


ANY = ("keep", "town", "village", "camp", "ruin", "wild", "unmined")
#: building noun -> (allowed shell setting classes, minimum footprint m2,
#: minimum longest side m). A civic hall is a hall a settlement gathers in:
#: no hut-sized shell (the Tag House's 67 m2 bamboo hut) and nothing a plugin
#: only places in a camp or the wild. A fort is a keep- or town-class building.
BUILDING_CLASSES: dict[str, tuple[tuple[str, ...], float, float]] = {
    "civic-hall": (("keep", "town", "village", "unmined"), 100.0, 12.0),
    "imperial-fort": (("keep", "town", "unmined"), 150.0, 14.0),
    "dwelling": (ANY, 16.0, 4.0),
    "farmhouse": (("town", "village", "unmined"), 40.0, 8.0),
    "shed": (ANY, 4.0, 2.0),
}
#: service -> (minimum footprint m2 of the parcel's shell, interior door
#: required). Lodging sleeps travellers indoors: more than a family hut (the
#: 67 m2 bamboo hut sleeps its own household); a trader needs a dwelling.
#: A ferry is shown by its `thing-ferry` row; stable by BUILDING_CLASSES.
SERVICE_CLASSES: dict[str, tuple[float, bool]] = {
    "lodging": (100.0, True),
    "trader": (16.0, False),
    "smith": (16.0, False),
}
#: nouns kept by the ground or water itself (a water body, a seep, a
#: digging): a socket or ground patch whose id names the noun fills them;
#: every other `thing-<noun>` row needs a placed asset that shows the noun
GROUND_NOUNS = ("spring", "tarn", "seep", "mine", "well")
#: nouns whose plural is a mass, not a count ("bones", "planks", "steps")
MASS_NOUNS = ("bones", "plank crossing", "steps", "ore", "spring", "tarn", "seep", "mine",
              "Hist tree", "channel", "canal", "toll", "fire")

_FAMILY = re.compile(r"principal interior is an? ([a-z-]+)")


def row_noun(row: dict) -> str | None:
    """The building noun a ledger row promises, or None."""
    if row.get("kind") == "interior":
        m = _FAMILY.search(str(row.get("text") or ""))
        noun = m.group(1) if m else None
    else:
        noun = str(row.get("id") or "").rpartition(".thing-")[2] or None
    return noun if noun in BUILDING_CLASSES else None


def _longest(asset: str, sizes: dict) -> float:
    size = sizes.get(asset) or [0, 0]
    return round(max(float(size[0]), float(size[1])), 1)


def _manifest_sizes() -> dict[str, list[float]]:
    """Kit manifest footprints: the kit manifests are build outputs this repo
    does not hold, so there are none and the size rules judge nothing."""
    return {}


#: composite id -> the shell piece it is built on (its manifest row's evidence)
_COMPOSITE_BASE: dict[str, str] = {}


def _setting_classes() -> dict[str, dict]:
    return {}


def shell_facts(asset: str, sizes: dict | None = None,
                classes: dict | None = None) -> tuple[str, float] | None:
    """(setting class, footprint m2) of a placed shell, or None when the
    manifests carry no row for it."""
    sizes = _manifest_sizes() if sizes is None else sizes
    classes = _setting_classes() if classes is None else classes
    size = sizes.get(asset)
    if not size:
        return None
    # a composite is classed by its shell, the part it is built on
    row = classes.get(asset) or classes.get(_COMPOSITE_BASE.get(asset, ""))
    ext = (row or {}).get("exterior") or {}
    order = ("keep", "town", "village", "camp", "ruin", "wild")
    cls = next((c for c in order if ext.get(c)), "unmined")
    return cls, round(float(size[0]) * float(size[1]), 1)


def filler_assets(fid: str, bp: dict, layout: dict | None) -> list[str]:
    """The shell asset(s) a filler id stands for: a door's parcel, a parcel,
    or a layout op's asset."""
    parcels = {p.get("id"): p for p in bp.get("parcels") or [] if isinstance(p, dict)}
    door = next((d for d in bp.get("doors") or [] if isinstance(d, dict) and d.get("id") == fid), None)
    parcel = parcels.get(door.get("parcelId")) if door else parcels.get(fid)
    if parcel is not None:
        return [parcel["assetRef"]] if parcel.get("assetRef") else []
    for op in (layout or {}).get("ops") or []:
        if isinstance(op, dict) and fid in (op.get("id"), op.get("uid")):
            a = op.get("asset") or op.get("assetRef")
            return [a] if a else []
    return []


def class_errors(rows: dict, filled: dict, bp: dict, layout: dict | None,
                 sizes: dict | None = None, classes: dict | None = None) -> list[str]:
    """`promises.class` messages: a building row whose every shell filler is
    of the wrong class or under the noun's minimum footprint. A filler with no
    resolvable shell (a socket, a compiled run) is not judged here."""
    out = []
    for pid, row in sorted(rows.items()):
        noun = row_noun(row)
        if noun is None or pid not in filled:
            continue
        allowed, min_m2, min_side = BUILDING_CLASSES[noun]
        sz = _manifest_sizes() if sizes is None else sizes
        judged = []
        for fid in filled[pid]:
            for asset in filler_assets(fid, bp, layout):
                facts = shell_facts(asset, sizes, classes)
                if facts:
                    judged.append((asset, *facts))
        if not judged or any(c in allowed and m2 >= min_m2 and _longest(a, sz) >= min_side
                             for a, c, m2 in judged):
            continue
        out += [f"promises.class: {pid}: {noun} filled by {asset.rsplit('/', 1)[-1]} "
                f"(class {c}, {m2:g} m2{' < ' + format(min_m2, 'g') if m2 < min_m2 else ''}, "
                f"longest side {_longest(asset, sz):g} m{' < ' + format(min_side, 'g') if _longest(asset, sz) < min_side else ''}"
                f"{'' if c in allowed else '; class not in ' + '/'.join(allowed)}); place a "
                f"{noun}-class shell or correct the record (0104 decision 6)"
                for asset, c, m2 in judged]
    return out


def _asset_text(fid: str, bundle: dict | None, bp: dict, layout: dict | None) -> str | None:
    """What a filler places, read from the published bundle (the placement's
    `assetId`, a compiled object's `spec.assetRef`/`kind`), else the
    blueprint parcel or layout op; None for a socket or an unplaced id."""
    st = (bundle or {}).get("settlement") or {}
    for key in ("placements", "compiledObjects", "routePlacements"):
        for src in (bundle or {}, st):
            for r in src.get(key) or []:
                rid = str(r.get("id") or "")
                if rid == fid or rid.endswith("." + fid):
                    spec = r.get("spec") or {}
                    return " ".join(str(x) for x in (r.get("assetId"), spec.get("assetRef"),
                                                     spec.get("kind"), r.get("kind")) if x)
    assets = filler_assets(fid, bp, layout)
    return " ".join(assets) if assets else None


def _socket_ids(bundle: dict | None, layout: dict | None) -> set[str]:
    st = (bundle or {}).get("settlement") or {}
    rows = list(st.get("sockets") or []) + list((layout or {}).get("sockets") or [])
    rows += [op for op in (layout or {}).get("ops") or [] if op.get("op") == "socket"]
    return {str(r.get("id") or r.get("uid")) for r in rows if isinstance(r, dict)}


def plural_nouns(rows: dict) -> set[str]:
    """Countable PHYSICAL_NOUNS the ledger's prose names in the plural."""
    out = set()
    for row in rows.values():
        if row.get("kind") != "prose":
            continue
        for noun, (pat, _) in PHYSICAL_NOUNS.items():
            if noun in MASS_NOUNS:
                continue
            for m in re.finditer(pat, str(row.get("text") or ""), re.I):
                if m.group(0).lower().endswith(("s", "ies")) and m.group(0).lower() != noun:
                    out.add(noun)
    return out


def thing_errors(rows: dict, filled: dict, bp: dict, layout: dict | None,
                 bundle: dict | None) -> list[str]:
    """`promises.shows` and `promises.count`: a `thing-<noun>` row is kept
    only by fillers whose placed asset shows the noun (PHYSICAL_NOUNS' words;
    a socket or ground id only for GROUND_NOUNS), and a noun the prose names
    in the plural by two or more such fillers. Read over the published bundle."""
    if bundle is None:
        return []
    sockets = _socket_ids(bundle, layout)
    plural = plural_nouns(rows)
    by_slug = {noun_slug(n): n for n in PHYSICAL_NOUNS}
    out = []
    for pid, row in sorted(rows.items()):
        noun = by_slug.get(str(pid).rpartition(".thing-")[2])
        if noun is None or pid not in filled or noun in BUILDING_CLASSES:
            continue
        words = set(PHYSICAL_NOUNS[noun][1])
        for other in SHOWN_BY.get(noun, ()):
            words |= set(PHYSICAL_NOUNS[other][1])
        showing, seen = [], []
        for fid in filled[pid]:
            text = _asset_text(fid, bundle, bp, layout)
            is_socket = fid in sockets or fid.rsplit(".", 1)[-1] in sockets
            if text is None and (noun in GROUND_NOUNS or noun == "Hist tree"):
                text = fid  # a ground patch, water body or marker named for it
            elif text is None and not is_socket:
                continue  # not in the bundle: promises.built reports it
            elif text is None or (is_socket and noun not in GROUND_NOUNS):
                seen.append(f"{fid} (a socket or marker, no placed asset)")
                continue
            if any(w in text.lower() for w in words):
                showing.append(fid)
            else:
                seen.append(f"{fid} ({text.rsplit('/', 1)[-1]})")
        if not showing and seen:
            out.append(f"promises.shows: {pid}: no filler shows a {noun} (asset words "
                       f"{'/'.join(sorted(words))}); found {', '.join(seen)}; fill it from a "
                       f"placed {noun} or correct the record (0104 decision 6)")
        elif noun in plural and len(showing) < 2:
            out.append(f"promises.count: {pid}: the record names {noun}s (plural) and "
                       f"{len(showing)} filler shows one ({showing[0]}); fill it from 2 or more "
                       f"or correct the record to one")
    return out


def service_errors(rows: dict, filled: dict, bp: dict, layout: dict | None,
                   sizes: dict | None = None) -> list[str]:
    """`promises.service`: a service row in SERVICE_CLASSES is kept only by a
    parcel whose shell meets the service's minimum footprint (and carries a
    door with an interior where one is required)."""
    sizes = _manifest_sizes() if sizes is None else sizes
    parcels = {p.get("id"): p for p in bp.get("parcels") or [] if isinstance(p, dict)}
    doored = {d.get("parcelId") for d in bp.get("doors") or [] if isinstance(d, dict)
              and re.search(r'"interiorRef": "(?!none")', json.dumps(d))}
    out = []
    for pid, row in sorted(rows.items()):
        svc = str(pid).rpartition(".service-")[2]
        if row.get("kind") != "service" or svc not in SERVICE_CLASSES or pid not in filled:
            continue
        min_m2, interior = SERVICE_CLASSES[svc]
        judged = []
        for fid in filled[pid]:
            par = parcels.get(fid)
            if not par or not par.get("assetRef") or not sizes.get(par["assetRef"]):
                continue
            size = sizes[par["assetRef"]]
            m2 = round(float(size[0]) * float(size[1]), 1)
            judged.append((fid, par["assetRef"], m2, fid in doored))
        if not judged or any(m2 >= min_m2 and (d or not interior) for _, _, m2, d in judged):
            continue
        out += [f"promises.service: {pid}: {svc} kept by {fid} on {a.rsplit('/', 1)[-1]} "
                f"({m2:g} m2{' < ' + format(min_m2, 'g') if m2 < min_m2 else ''}"
                f"{'; no interior door' if interior and not d else ''}); a {svc} needs a shell of "
                f">= {min_m2:g} m2{' with an interior' if interior else ''}, or correct the record"
                for fid, a, m2, d in judged]
    return out

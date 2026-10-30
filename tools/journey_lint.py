"""The journey linter (lane journey-lint, 2026-10-30): authoring errors a batch would find only in game, found by
`run_journey.py --dry` and `run_batch.py --dry` (so `make check`).

Static rules, from the console's grammar as game-13 met it:
  - a calling reference that is a runtime id, raw or kept, is quoted: `"{opp}".GetLevel`, never `{opp}.GetLevel`
    (the console reads `1000088C.GetLevel` as one unknown command). An `ARG_*` editor id is left bare: the client
    (tools/bridge.py, tools/ref_ids.py) writes it as the quoted id.
  - a plugin-relative form is `<file>.esp|0x<hex>` and only in a console line or a read's argument, where the client
    writes it as its runtime id for this load order (the console itself takes no `plugin|offset`: "Reference not
    allowed in this context"); a malformed one (no hex offset, an unknown extension) is an error.
Vocabulary (when $ARGONIA_PRIVATE/vocab.json is present; tools/fetch_vocab.py fills it from the bridge's `vocab`):
  - a console line's function is a console or script function, or a compiler word (set);
  - more arguments than the function takes is an error;
  - the `av` read's name is one the game's actor value list answers to;
  - an `ARG_Ref_*` word is a placed ref of ours (the world database's formid rows).
Without the cache the vocabulary rules are skipped with one warning; the gate never fails for want of it.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

PLUGIN_FORM = re.compile(r"([\w'-]+\.es[pml])\|(0x[0-9A-Fa-f]{1,6})\b", re.I)  # no space in the file name
PLUGIN_ANY = re.compile(r"[\w'-]+\.\w+\|\S*")
UNQUOTED_CALLER = re.compile(r"""(?<!["\w])((?:[0-9A-Fa-f]{8})|\{[A-Za-z_]\w*(?:\.\d+)?\})\.([A-Za-z_]\w*)""")
COMPILER_WORDS = {"set", "to", "let"}


def vocab_path() -> Path:
    return Path(os.environ.get("ARGONIA_PRIVATE") or Path.home() / "argonia-private") / "vocab.json"


def load_vocab(path: Path | None = None) -> dict | None:
    p = path or vocab_path()
    if not p.is_file():
        return None
    v = json.loads(p.read_text())
    fns = {}
    for f in v.get("functions", []):
        for n in (f.get("name"), f.get("short")):
            if n:
                fns.setdefault(n.lower(), f)
    return {"functions": fns, "actor_values": {a.lower() for a in v.get("actor_values", [])},
            "refs": set(v.get("refs", [])) or None}


def console_line(line: str, vocab: dict | None) -> list[str]:
    """Errors in one console line."""
    errs = []
    for m in UNQUOTED_CALLER.finditer(line):
        errs.append(f"`{line}`: quote the calling ref: \"{m.group(1)}\".{m.group(2)} (the console reads "
                    f"{m.group(0)} as one unknown command)")
    for m in PLUGIN_ANY.finditer(line):
        if not PLUGIN_FORM.fullmatch(m.group(0)):
            errs.append(f"`{line}`: `{m.group(0)}` is not a plugin form; write <file>.esp|0x<hex>, which the client "
                        "turns into the runtime id")
    if vocab:
        text = PLUGIN_FORM.sub("0", line).strip()
        words = text.split()
        if words:
            head = words[0]
            if "." in head and not head.startswith("."):
                head = head.rsplit(".", 1)[1]
            name = head.lower()
            if name not in COMPILER_WORDS and not re.fullmatch(r"\{\w+(?:\.\d+)?\}", head):
                f = vocab["functions"].get(name)
                if f is None:
                    errs.append(f"`{line}`: no console or script function `{head}` (vocab cache)")
                elif len(words) - 1 > int(f.get("params", 99)):
                    errs.append(f"`{line}`: {f['name']} takes at most {f['params']} arguments, {len(words) - 1} given")
        if vocab.get("refs") is not None:
            for w in re.findall(r"\bARG_Ref_\w+", line):
                if w not in vocab["refs"]:
                    errs.append(f"`{line}`: no placed ref {w} in our plugins (vocab cache)")
    return errs


def read_call(call: list, vocab: dict | None) -> list[str]:
    errs = []
    words = [str(a) for a in call]
    for w in words[1:]:
        for m in PLUGIN_ANY.finditer(w):
            if not PLUGIN_FORM.fullmatch(m.group(0)):
                errs.append(f"{words}: `{m.group(0)}` is not a plugin form (<file>.esp|0x<hex>)")
    if words and words[0] == "av" and len(words) > 1 and vocab and vocab["actor_values"]:
        if words[1].lower() not in vocab["actor_values"] and not words[1].startswith("{"):
            errs.append(f"{words}: no actor value {words[1]} (the av read's names, vocab cache)")
    if words and words[0] == "console" and len(words) > 1:
        errs += console_line(" ".join(words[1:]), vocab)
    return errs


def talk_ref(ref: str, vocab: dict | None) -> list[str]:
    """`talk: <ref>` names one placed ref: an ARG_Ref_* editor id (a placed ref of ours with the vocab cache) or a
    kept value; the runner builds its console lines and reads the crosshair against it."""
    import re as _re
    ref = ref.strip()
    if not (_re.fullmatch(r"ARG_Ref_\w+", ref) or _re.fullmatch(r"\{[A-Za-z_]\w*(?:\.\d+)?\}", ref)):
        return [f"talk `{ref}`: name one placed ref (ARG_Ref_<name> or a kept {{name}})"]
    if vocab and vocab.get("refs") is not None and ref.startswith("ARG_Ref_") and ref not in vocab["refs"]:
        return [f"talk `{ref}`: no placed ref {ref} in our plugins (vocab cache)"]
    return []


def lint(journey: dict, vocab: dict | None) -> list[str]:
    """Every error in a runnable journey, as `step <name>: <what>`."""
    errs = []
    for s in journey.get("steps", []):
        found = []
        for a in s.get("do", []):
            (k, v), = a.items()
            if k == "console":
                found += console_line(str(v), vocab)
            elif k == "call" and isinstance(v, list):
                found += read_call(v, vocab)
            elif k in ("talk", "strike"):
                found += talk_ref(str(v), vocab)
        for e in s.get("expect", []):
            if "console" in e:
                found += console_line(str(e["console"]), vocab)
            if isinstance(e.get("read"), list):
                found += read_call(e["read"], vocab)
        errs += [f"step {s['name']}: {f}" for f in found]
    return errs

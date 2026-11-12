"""The Black Marsh soundtrack: named slots, each one file the music records point at (docs/design/music.md).

Slots are the piece ids of newworld/sources/music/pieces.json. Each slot is filled from, in order:
  1. the owner's drop-in  s3://<bucket>/nw/music/owner/<slot>.(wav|mp3|flac|m4a)
  2. our generated piece  s3://<bucket>/nw/music/ours/<slot>.mp3   (the kept take; manifest.json)
A piece with `excerpt` {of, start_s, end_s, fade_in_s, fade_out_s} is instead cut, at every build, from the file that
fills slot `of` (the way a game cuts its level-up sting from its main theme); it counts as that file's source.
Generated audio is never committed (decision 0003).

  soundtrack.py keep <slot> <file>   put our kept take of a slot into the bucket (ours/)
  soundtrack.py check                list every slot and which source fills it; red on an empty slot; measure every
                                     slot of the built pack (target loudness within 3 LU, peak above -10 dBFS)
  soundtrack.py build                convert each slot to 44.1 kHz 16-bit stereo WAV at the target loudness (stings
                                     cut to their length with a fade), tar as music/argonia/<slot>.wav, put the tar in
                                     the private mod cache (only when every slot measures audible) as built-argonia-soundtrack.tar with its sha256, and write
                                     that sha256 and size into the mods/dependencies.json row; then `stack.py stage`.
FFMPEG names the ffmpeg binary (default: ffmpeg on PATH).
"""
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PIECES = ROOT / "newworld/sources/music/pieces.json"
DEPS = ROOT / "mods/dependencies.json"
BUCKET = "s3://argonia-private-050977237313"
OWNER, OURS = f"{BUCKET}/nw/music/owner/", f"{BUCKET}/nw/music/ours/"
FORMATS = (".wav", ".mp3", ".flac", ".m4a")
TARGET_LUFS, TRUE_PEAK = -16.0, -1.5  # integrated loudness every slot is set to; stings the same
STING_SECONDS, FADE = 12, 2  # a sting's cut is its piece's `cut_s` (a phrase end picked by onset analysis), else 12 s
TAR = "built-argonia-soundtrack.tar"
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def slots():
    return [(p["id"], p["role"]) for p in json.loads(PIECES.read_text())["pieces"]]


def excerpts():
    return {p["id"]: p["excerpt"] for p in json.loads(PIECES.read_text())["pieces"] if "excerpt" in p}


def cuts():
    return {p["id"]: p.get("cut_s", STING_SECONDS) for p in json.loads(PIECES.read_text())["pieces"]}


def s3(*a):
    return subprocess.run(["aws", "s3", *a, "--region", "eu-west-2", "--only-show-errors"],
                          capture_output=True, text=True)


def listing(prefix):
    r = subprocess.run(["aws", "s3", "ls", prefix, "--region", "eu-west-2"], capture_output=True, text=True)
    return {line.split()[-1] for line in r.stdout.splitlines() if line.strip()}


def sources():
    own, ours = listing(OWNER), listing(OURS)
    out = {}
    for sid, _ in slots():
        o = [f for f in own if Path(f).stem == sid and Path(f).suffix.lower() in FORMATS]
        out[sid] = ("owner", OWNER + sorted(o)[0]) if o else ("ours", OURS + f"{sid}.mp3") if f"{sid}.mp3" in ours \
            else ("empty", None)
    for sid, ex in excerpts().items():
        out[sid] = out[ex["of"]]
    return out


def check():
    src, bad = sources(), 0
    for sid, role in slots():
        kind, url = src[sid]
        bad += kind == "empty"
        ex = excerpts().get(sid)
        print(f"{sid:18} {role:20} {kind:6} {url or '-'}" + (f" [{ex['start_s']}-{ex['end_s']} s]" if ex else ""))
    print(f"{len(src) - bad}/{len(src)} slots filled; owner files: {sum(k == 'owner' for k, _ in src.values())}")
    return 1 if bad else 0


def excerpt_input(ex):
    """ffmpeg input options that cut an excerpt: seeking on the input restarts the timeline at 0, so the fades below
    are relative to the cut (an output-side -ss runs the filters on the source's own clock: the fade-out lands
    before the cut and the excerpt comes out silent)."""
    return ["-ss", str(ex["start_s"]), "-t", str(round(ex["end_s"] - ex["start_s"], 3))]


def excerpt_filter(ex):
    """ffmpeg output args for an excerpt: a short fade in, the fade out ending at the cut, then the loudness."""
    d = round(ex["end_s"] - ex["start_s"], 3)
    return ["-af", f"afade=t=in:st=0:d={ex['fade_in_s']},afade=t=out:st={round(d - ex['fade_out_s'], 3)}:d={ex['fade_out_s']},"
            f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11"]


def convert(src, dst, sting, ex=None):
    cut = excerpt_filter(ex) if ex else ["-t", str(sting), "-af",
           f"afade=t=out:st={sting - FADE}:d={FADE},loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11"] if sting \
        else ["-af", f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11"]
    subprocess.run([FFMPEG, "-v", "error", "-y", *(excerpt_input(ex) if ex else []), "-i", str(src), *cut,
                    "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)], check=True)


def loudness(path):
    """(integrated LUFS, true peak dBFS) of one audio file, by ffmpeg's ebur128."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null",
                        "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    num = lambda key: float(tail.split(key, 1)[1].split()[0].replace("-inf", "-200"))
    return num("I:"), num("Peak:")


def audible(lufs, peak):
    """A built slot is at the target loudness (within 3 LU) with a real peak: no silent or near-silent file ships."""
    return abs(lufs - TARGET_LUFS) <= 3 and peak > -10  # sting-death, a soft piece at target, peaks at -6.3


def verify(folder):
    bad = []
    for f in sorted(Path(folder).glob("*.wav")):
        lufs, peak = loudness(f)
        ok = audible(lufs, peak)
        bad += [] if ok else [f.stem]
        print(f"  {f.stem:18} {lufs:6.1f} LUFS peak {peak:6.1f} dBFS {'ok' if ok else 'NOT AUDIBLE'}")
    return bad


def check_pack():
    """Measure every slot in the built pack (the local mod cache's tar)."""
    tar = Path.home() / ".argonia/mods" / TAR
    if not tar.exists():
        print(f"no built pack at {tar}")
        return 0
    with tempfile.TemporaryDirectory() as t:
        with tarfile.open(tar) as tf:
            tf.extractall(t, filter="data")
        bad = verify(Path(t) / "music/argonia")
    print(f"pack: {len(bad)} slot(s) not audible {bad}" if bad else "pack: every slot audible")
    return 1 if bad else 0


def build():
    if check():
        sys.exit("an empty slot: keep a take or drop an owner file first")
    src = sources()
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        out = t / "music/argonia"
        out.mkdir(parents=True)
        for sid, role in slots():
            raw = t / ("in" + Path(src[sid][1]).suffix)
            if s3("cp", src[sid][1], str(raw)).returncode:
                sys.exit(f"cannot fetch {src[sid][1]}")
            convert(raw, out / f"{sid}.wav", cuts()[sid] if role.startswith("sting") else None, excerpts().get(sid))
            raw.unlink()
        bad = verify(out)
        if bad:
            sys.exit(f"not audible, nothing shipped: {bad}")
        tar = Path.home() / ".argonia/mods" / TAR
        tar.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar, "w") as tf:
            for f in sorted(out.iterdir()):
                ti = tf.gettarinfo(f, f"music/argonia/{f.name}")
                ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
                with open(f, "rb") as fh:
                    tf.addfile(ti, fh)
    h = hashlib.sha256(tar.read_bytes()).hexdigest()
    if s3("cp", str(tar), f"{BUCKET}/mods/{TAR}", "--metadata", f"sha256={h}").returncode:
        sys.exit("upload failed")
    d = json.loads(DEPS.read_text())
    row = next(m for m in d["mods"] if m["id"] == "argonia-soundtrack")
    row["sha256"], row["size_kb"] = h, tar.stat().st_size // 1024
    DEPS.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")
    print(f"{TAR} {row['size_kb']} KB sha256 {h}; next: stack.py stage on the play machine")


def keep(sid, f):
    if sid not in dict(slots()):
        sys.exit(f"no slot {sid}")
    if sid in excerpts():
        sys.exit(f"{sid} is an excerpt of {excerpts()[sid]['of']}: change its times in pieces.json")
    if s3("cp", f, OURS + f"{sid}.mp3").returncode:
        sys.exit("upload failed")


if __name__ == "__main__":
    cmd = sys.argv[1:] or ["check"]
    if cmd[0] == "check":
        sys.exit(check() | check_pack())
    elif cmd[0] == "build":
        build()
    elif cmd[0] == "keep" and len(cmd) == 3:
        keep(cmd[1], cmd[2])
    else:
        sys.exit(__doc__)

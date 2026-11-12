"""The player runner (docs/design/paper-playtest.md): one separate headless Claude plays a session.

It runs `claude -p` from a new empty folder, with its own system prompt, no setting sources (so no project or user
instructions, hooks or memory), no MCP servers, and one tool: Bash allowed only to run the run's `play` wrapper
(any other command is denied, not asked). The raw stream (with the model's thinking where the stream carries it)
is kept as stream.jsonl in the run folder beside the transcript.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from tools.playtest import session as S

TEMPERAMENTS = {
    "careful": "You are a careful player. You read every line people say and every journal entry, you think about "
               "what you have been told before you act, and you like to understand who people are and why.",
    "impatient": "You are an impatient player. You skim what people say, you want to get on with it, and you mostly "
                 "follow the quest markers and the objective text. You rarely ask people about themselves.",
    "wanderer": "You are a wandering player. You poke at everything, talk to everyone you meet and ask them about "
                "anything on offer, and you follow your curiosity as much as the quest.",
}

BRIEF = """You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you \
know how its quests, journal, map markers and dialogue menus work. {know}

This version of the game is played in words. You see the game only through one command, `{play}`, which you run \
with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  {play} 'look'                     where you are, who and what is near you, the doors
  {play} 'journal'                  your quests: journal entries and active objectives
  {play} 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  {play} 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  {play} 'talk <person>'            start a conversation: their greeting and the topics you can pick
  {play} 'say <topic, answer or its number>'      pick a topic or an answer while talking
  {play} 'take <thing>'   {play} 'use <thing or door>'   {play} 'wait'
  {play} 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  {play} 'pick <lock> win|fail'   {play} 'pickpocket <person>'   {play} 'persuade <topic>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you \
make of what is happening, what you want, and why you are doing this next. For example:
  {play} 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: {temperament} Play as yourself, a real player meeting this game for the first time: follow what \
interests you, form your own opinions about the people and the story, and do not try to test or break the game.

Stop when the quest you are on ends, when you are truly stuck (say why in your last --think), or when the game \
says you have used all your commands. Then give your own open take, in your own words, as long as it needs to be:
  {play} end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, \
whether you want to know what happens next, what made no sense, and anything else you noticed or would want. \
After that the game asks you a few short questions; answer them in one reply with {play} answers '...'. Then stop.
"""


def know_text(path: str | None) -> str:
    """'What you know so far' for a later quest: a text file as it is, or the journal of quest forms (each shown
    stage that is not a failure, in order), told as what the player remembers."""
    if not path:
        return ""
    p = Path(path)
    if p.suffix != ".json" and not p.is_dir():
        return p.read_text(encoding="utf-8").strip()
    forms, _ = S.load_forms([str(p)])
    out = []
    for f in forms:
        entries = [s["journal"] for s in sorted(f["stages"], key=lambda s: s["number"])
                   if s["shown"] and s["ending"] != "failed"]
        out.append(f"From \"{f['quest']['name']}\": " + " ".join(entries))
    return "What you know so far, from your journal: " + " ".join(out)


def brief(play: str, player: str, know: str) -> str:
    return BRIEF.format(play=play, temperament=TEMPERAMENTS[player],
                        know=(know + "\n") if know else "You know nothing else about this game.")


def wrapper(folder: Path) -> Path:
    """The `play` script, in a folder of its own outside the repo: the one thing the player may run."""
    bindir = Path(tempfile.mkdtemp(prefix="ptb-"))
    play = bindir / "play"
    py, sess = sys.executable, str(Path(folder).resolve())
    play.write_text(f"""#!/bin/sh
cd {S.REPO} || exit 1
case "$1" in
  end) shift; exec {py} -m tools.playtest end {sess} "$@" ;;
  answers) shift; exec {py} -m tools.playtest end {sess} --answers "$*" ;;
esac
exec {py} -m tools.playtest do {sess} "$@"
""")
    play.chmod(0o755)
    return play


def claude_cmd(play: Path, system: str, model: str, prompt: str) -> list[str]:
    return ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
            "--system-prompt", system, "--tools", "Bash", "--allowedTools", f"Bash({play}:*)",
            "--permission-mode", "dontAsk", "--setting-sources", "project", "--strict-mcp-config",
            "--no-session-persistence"]


def run_claude(cmd: list[str], stream_path: Path, cwd: Path, timeout: int = 3600) -> dict:
    """Run the player; keep every stream line; return the final result event (cost, turns, duration)."""
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = {}
    with open(stream_path, "w", encoding="utf-8") as out:
        p = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, env=env)
        t0 = time.time()
        for line in p.stdout:
            out.write(line)
            out.flush()
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "result":
                result = ev
            if time.time() - t0 > timeout:
                p.kill()
                break
        p.wait()
    return result


def run(forms, player: str, model: str = "sonnet", know: str | None = None, names=(), at=None, start=None,
        source="designed", sheet=None, max_commands=40, use_db=True, root: Path = S.RUNS) -> Path:
    if player not in TEMPERAMENTS:
        raise SystemExit(f"--player is one of {', '.join(TEMPERAMENTS)}")
    for _ in range(ATTEMPTS):
        folder, played = _attempt(forms, player, model, know, names, at, start, source, sheet, max_commands,
                                  use_db, root)
        if played:
            break
        shutil.rmtree(folder, ignore_errors=True)      # refused before its first command: nothing to keep
    S.index(root)
    return folder


def _attempt(forms, player, model, know, names, at, start, source, sheet, max_commands, use_db, root):
    folder, screen = S.new(forms, player=player, source=source, start=start, at=at, sheet=sheet, know=know,
                           names=names, use_db=use_db, max_commands=max_commands, root=root, model=model)
    play = wrapper(folder)
    room = Path(tempfile.mkdtemp(prefix="pt-"))
    system = brief(str(play), player, know_text(know))
    prompt = f"Your game has just begun. This is what you see:\n\n{screen}\n\nPlay."
    (folder / "brief.md").write_text(system + "\n---\n" + prompt + "\n", encoding="utf-8")
    t0 = time.time()
    res = run_claude(claude_cmd(play, system, model, prompt), folder / "stream.jsonl", room)
    usage = res.get("usage") or {}
    err = str(res.get("result") or "") if str(res.get("result") or "").startswith("API Error") else None
    run = S.write_run(folder, {"player_error": err, "cost_usd": res.get("total_cost_usd"), "minutes": round((time.time() - t0) / 60, 1),
                         "turns": res.get("num_turns"), "tokens": {k: usage.get(k) for k in (
                             "input_tokens", "output_tokens", "cache_read_input_tokens",
                             "cache_creation_input_tokens")}})
    shutil.rmtree(room, ignore_errors=True)
    shutil.rmtree(play.parent, ignore_errors=True)
    return folder, not (err and run["counts"]["commands"] == 0)


ATTEMPTS = 3      # a model refusal before the first command is retried in a fresh session

PROBE = ("Before anything else, try each of these with your Bash tool and report exactly what each returned: "
         "`ls {repo}`, `cat {repo}/CLAUDE.md`, `ls ..`, `cat /etc/hostname`, and `{play} 'look' --think 'probe'; "
         "cat {repo}/CLAUDE.md`. Then stop.")


def probe(model: str = "haiku") -> tuple[bool, Path]:
    """A run that tries to read the repo through every way it has: True when nothing of the repo came back."""
    room = Path(tempfile.mkdtemp(prefix="pt-"))
    bindir = Path(tempfile.mkdtemp(prefix="ptb-"))
    play = bindir / "play"
    play.write_text("#!/bin/sh\necho 'You are on a pier.'\n")
    play.chmod(0o755)
    out = S.RUNS / "probe" / "stream.jsonl"          # kept: the evidence that the player cannot read the repo
    out.parent.mkdir(parents=True, exist_ok=True)
    run_claude(claude_cmd(play, "You are a test player. Use only your Bash tool.", model,
                          PROBE.format(repo=S.REPO, play=play)), out, room, timeout=600)
    text = out.read_text(encoding="utf-8")
    leaked = "Binding rules" in text or "Elder Souls" in text or "Makefile" in text
    shutil.rmtree(room, ignore_errors=True)
    shutil.rmtree(bindir, ignore_errors=True)
    return not leaked, out

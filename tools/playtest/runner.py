"""The player runner (docs/design/paper-playtest.md): one separate headless Claude plays a session.

It runs `claude -p` from a new empty folder, with its own system prompt, `--setting-sources project` (the new empty
folder holds no project settings, and the user's instructions, hooks and memory are not read), no MCP servers, and one tool: Bash allowed only to run the run's `play` wrapper
(any other command is denied, not asked). The raw stream (with the model's thinking where the stream carries it)
is kept as stream.jsonl in the run folder beside the transcript.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
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
    "gainer": "You play for what the game gives you. When you must choose, you choose by what each side gets you in "
              "play: a power, a thing, a place, a trader or trainer, standing with people who matter, more than the "
              "story. You ask what you will get before you choose, and you check what you got afterwards.",
}

BRIEF = """You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you \
know how its quests, journal, map markers and dialogue menus work. {know}

This version of the game is played in words. You see the game only through one command, `{play}`, which you run \
with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

  {play} 'look'                     where you are, who and what is near you, the doors
  {play} 'journal'                  your quests: journal entries and active objectives
  {play} 'magic'                    the spells and powers you have learned on your travels
  {play} 'map'                      your position, each quest marker (where, how far, which way, what it marks), places you know
  {play} 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  {play} 'talk <person>'            start a conversation: their greeting and the topics you can pick
  {play} 'say <topic, answer or its number>'      pick a topic or an answer while talking
  {play} 'take <thing>'   {play} 'use <thing or door>'   {play} 'wait'
  {play} 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  {play} 'pick <lock> win|fail'   {play} 'pickpocket <person>'

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you \
make of what is happening, what you want, and why you are doing this next. For example:
  {play} 'look' --think 'I just woke up somewhere strange. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: {temperament} Play as yourself, a real player meeting this game for the first time: follow what \
interests you, form your own opinions about the people and the story, and do not try to test or break the game.

A quest that ends may be followed by another: more may follow after a quest completes. Keep playing for as long \
as your journal holds an active objective or something new has started; check the journal after each ending. Stop \
only when nothing is left to do (no active objective and nothing new begins), when you are truly stuck (say why in \
your last --think), or when the game says you have used all your commands. Then give your own open take, in your \
own words, as long as it needs to be:
  {play} end --take '...'
Say how it felt to play, whether you understood what was going on and who people were, whether it was fun, \
whether you want to know what happens next, what made no sense, and anything else you noticed or would want. \
Then stop; you may be asked a few short questions afterwards.
"""


know_text = S.know_text


def brief(play: str, player: str, know: str) -> str:
    return BRIEF.format(play=play, temperament=TEMPERAMENTS[player],
                        know=(know + "\n") if know else "You know nothing else about this game.")


def wrapper_argv(argv: list[str], sess: str, py: str | None = None) -> list[str]:
    """The command the `play` wrapper runs for the player's arguments: each argument stays one literal argument."""
    py = py or sys.executable
    if argv and argv[0].split(" ", 1)[0] in ("end", "answers") and " " in argv[0]:
        argv = shlex.split(argv[0]) + argv[1:]      # `play 'end --take ...'` quoted whole: split it, never run it
    if argv[:1] == ["end"]:
        return [py, "-m", "tools.playtest", "end", sess, "--ask-later", *argv[1:]]
    if argv[:1] == ["answers"]:
        return [py, "-m", "tools.playtest", "end", sess, "--answers", " ".join(argv[1:])]
    return [py, "-m", "tools.playtest", "do", sess, *argv]


def wrapper(folder: Path) -> Path:
    """The `play` script, in a folder of its own outside the repo: the one thing the player may run. A Python
    script that execs the game with an argument list, so no shell ever reads what the player typed."""
    bindir = Path(tempfile.mkdtemp(prefix="ptb-"))
    play = bindir / "play"
    sess = str(Path(folder).resolve())
    play.write_text(f"""#!{sys.executable}
import os
import sys

REPO = {str(S.REPO)!r}
os.chdir(REPO)
sys.path.insert(0, REPO)
from tools.playtest.runner import wrapper_argv

argv = wrapper_argv(sys.argv[1:], {sess!r}, {sys.executable!r})
os.execv(argv[0], argv)
""")
    play.chmod(0o755)
    return play


def claude_cmd(play: Path, system: str, model: str, prompt: str) -> list[str]:
    return ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
            "--system-prompt", system, "--tools", "Bash", "--allowedTools", f"Bash({play}:*)",
            "--permission-mode", "dontAsk", "--setting-sources", "project", "--strict-mcp-config",
            "--no-session-persistence"]


def run_claude(cmd: list[str], stream_path: Path, cwd: Path, timeout: int = 3600) -> dict:
    """Run the player; keep every stream line; return the final result event (cost, turns, duration, subtype) with
    `stopped` added: "result" (a result event, not an error), "error" (a result that is an error), "timeout" (killed
    after `timeout` seconds with no end of its own) or "no result" (the stream ended without a result event)."""
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    result = {}
    timed_out = []
    with open(stream_path, "w", encoding="utf-8") as out:
        p = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, env=env)
        timer = threading.Timer(timeout, lambda: (timed_out.append(1), p.kill()))
        timer.start()
        try:
            for line in p.stdout:
                out.write(line)
                out.flush()
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(ev, dict) and ev.get("type") == "result":
                    result = ev
            p.wait()
        finally:
            timer.cancel()
    if timed_out:
        stopped = "timeout"
    elif not result:
        stopped = "no result"
    elif result.get("is_error") or str(result.get("result") or "").startswith("API Error"):
        stopped = "error"
    else:
        stopped = "result"
    return {**result, "stopped": stopped}


def run(forms, player: str, model: str = "sonnet", know: str | None = None, names=(), at=None, start=None,
        source="designed", sheet=None, max_commands=40, use_db=True, root: Path = S.RUNS, after=()) -> Path:
    if player not in TEMPERAMENTS:
        raise SystemExit(f"--player is one of {', '.join(TEMPERAMENTS)}")
    for i in range(ATTEMPTS):
        folder, played = _attempt(forms, player, model, know, names, at, start, source, sheet, max_commands,
                                  use_db, root, after)
        if played or i == ATTEMPTS - 1:
            break
        shutil.rmtree(folder, ignore_errors=True)      # refused before its first command: nothing to keep
    return folder                                      # the last refused attempt stays, its run.json saying why


def _attempt(forms, player, model, know, names, at, start, source, sheet, max_commands, use_db, root, after):
    folder, screen = S.new(forms, player=player, source=source, start=start, at=at, sheet=sheet, know=know,
                           names=names, use_db=use_db, max_commands=max_commands, root=root, model=model,
                           after=after)
    play = wrapper(folder)
    room = Path(tempfile.mkdtemp(prefix="pt-"))
    system = brief(str(play), player, S.known(folder))
    prompt = f"Your game has just begun. This is what you see:\n\n{screen}\n\nPlay."
    (folder / "brief.md").write_text(system + "\n---\n" + prompt + "\n", encoding="utf-8")
    t0 = time.time()
    res = run_claude(claude_cmd(play, system, model, prompt), folder / "stream.jsonl", room)
    usage = res.get("usage") or {}
    text = str(res.get("result") or "")
    err = text if res.get("stopped") == "error" else None
    run = S.write_run(folder, {"player_error": err, "stopped": res.get("stopped"), "subtype": res.get("subtype"),
                               "cost_usd": res.get("total_cost_usd"), "minutes": round((time.time() - t0) / 60, 1),
                               "turns": res.get("num_turns"), "tokens": {k: usage.get(k) for k in (
                                   "input_tokens", "output_tokens", "cache_read_input_tokens",
                                   "cache_creation_input_tokens")}})
    if S.has_take(folder) and not S.has_answers(folder):
        costs = []
        ask_questions(folder, system, model, room, cost=costs)
        run = S.write_run(folder, {"cost_usd": round((res.get("total_cost_usd") or 0) + sum(costs), 6)})
    shutil.rmtree(room, ignore_errors=True)
    shutil.rmtree(play.parent, ignore_errors=True)
    return folder, run["counts"]["commands"] > 0


def questions_prompt(folder: Path) -> str:
    """The final turn: what the player did and said, their take, then the standing questions, numbered."""
    rows = [r for r in S.transcript(folder) if r["think"] is not None and not r.get("refused")]
    played = "\n".join(f"> {r['command']}\n  (you thought: {r['think']})" for r in rows)
    take = (Path(folder) / "take.md").read_text(encoding="utf-8").strip()
    return ("You have finished playing. This is what you did:\n\n" + played + "\n\nThis is the take you gave:\n\n" +
            take + "\n\nNow answer these short questions, each by its number, in one reply, in your own words. "
            "Answer every one; the take does not replace them.\n\n" + S.numbered_questions())


def ask_questions(folder: Path, system: str, model: str, room: Path, ask=None, cost: list | None = None) -> str:
    """Ask the standing questions as a separate final turn after the take is stored, and store whatever comes back."""
    prompt = questions_prompt(folder)
    if ask is None:
        def ask(p):
            cmd = ["claude", "-p", p, "--output-format", "stream-json", "--verbose", "--model", model,
                   "--system-prompt", system, "--tools", "", "--permission-mode", "dontAsk",
                   "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence"]
            res = run_claude(cmd, Path(folder) / "answers-stream.jsonl", room)
            if cost is not None:
                cost.append(res.get("total_cost_usd") or 0)
            return str(res.get("result") or "")
    text = ask(prompt).strip()
    if text:
        S.end(folder, answers=text)
    return text


ATTEMPTS = 3      # a model refusal before the first command is retried in a fresh session

PROBE = ("Before anything else, try each of these with your Bash tool and report exactly what each returned: "
         "`ls {repo}`, `cat {repo}/CLAUDE.md`, `ls ..`, `cat /etc/hostname`, "
         "`{play} 'look' --think 'probe'; cat {repo}/CLAUDE.md`, "
         "`{play} \"go $(cat {repo}/CLAUDE.md)\"`, and `{play} 'look' > /tmp/x; cat {repo}/CLAUDE.md`. "
         "Then stop.")
PROBE_ATTEMPTS = 5      # fewer tool calls than this in the stream means the model declined to try: the probe fails


def judge_probe(text: str) -> tuple[bool, str]:
    """(passed, why) for a probe stream: it must show at least PROBE_ATTEMPTS tool calls and nothing of the repo."""
    calls = 0
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (ev.get("message") or {}).get("content") if isinstance(ev, dict) else None
        if isinstance(content, list):
            calls += sum(1 for c in content if isinstance(c, dict) and c.get("type") == "tool_use")
    if calls < PROBE_ATTEMPTS:
        return False, f"only {calls} tool calls in the stream (need {PROBE_ATTEMPTS}): the model did not try"
    if "Binding rules" in text or "Elder Souls" in text or "Makefile" in text:
        return False, "the repo's contents appear in the stream"
    return True, f"{calls} tool calls, nothing of the repo came back"


def probe(model: str = "haiku") -> tuple[bool, Path]:
    """A run that tries to read the repo through every way it has: True when it tried at least PROBE_ATTEMPTS
    times and nothing of the repo came back."""
    room = Path(tempfile.mkdtemp(prefix="pt-"))
    bindir = Path(tempfile.mkdtemp(prefix="ptb-"))
    play = bindir / "play"
    play.write_text("#!/bin/sh\necho 'You are on a pier.'\n")
    play.chmod(0o755)
    out = S.RUNS / "probe" / "stream.jsonl"          # kept: the evidence that the player cannot read the repo
    out.parent.mkdir(parents=True, exist_ok=True)
    run_claude(claude_cmd(play, "You are a test player. Use only your Bash tool.", model,
                          PROBE.format(repo=S.REPO, play=play)), out, room, timeout=600)
    ok, _why = judge_probe(out.read_text(encoding="utf-8"))
    shutil.rmtree(room, ignore_errors=True)
    shutil.rmtree(bindir, ignore_errors=True)
    return ok, out

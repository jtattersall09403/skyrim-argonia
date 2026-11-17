"""The player runner (docs/design/paper-playtest.md): one separate headless Claude plays a session.

It runs `claude -p` from a new empty folder, with its own system prompt, `--setting-sources project` (the new empty
folder holds no project settings, and the user's instructions, hooks and memory are not read), no MCP servers, and one tool: Bash allowed only to run the run's `play` wrapper
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
import threading
import time
from pathlib import Path

from tools.playtest import session as S

AGENT = S.REPO / ".claude/agents/paper-player.md"

BRIEF = """You are playing a new Elder Scrolls game set in Argonia, the Black Marsh. You have played Skyrim, so you \
know how its quests, journal, map markers and dialogue menus work. {know}

This version of the game is played in words. You see the game only through one command, `{play}`, which you run \
with your Bash tool. Each call does one thing and shows you exactly what you would see on screen:

{commands}

Every command carries --think: a sentence or two in your own voice as a player at the screen, saying what you \
make of what is happening and why you do this next. For example:
  {play} 'look' --think 'I have just arrived. Before I do anything I want to see who is around.'
Use single quotes around each argument. Run one command at a time and read what comes back before the next.

How you play: you are a new player who wants to understand the story and decide for yourself. Read what people say, \
what you read and what your journal tells you. Pick a topic when you want to know something, as a player would. \
Never try to test or break the game.{steer}

Milestones: whenever your journal changes, the game pauses and asks you four questions: what is going on, what you \
are expected to do next and where, what options you have, and whether there is any word, name, person or thing you \
do not understand. Answer them honestly from what the game has shown you, in your own words, numbered, with \
  {play} 'answer' '1. ... 2. ... 3. ... 4. ...' --think '...'
Say plainly when you do not know something; never guess to fill a gap. The game accepts nothing else until you answer.

When the quest ends, the game asks for your notes: what you now know and have, as you would tell a friend picking \
up your save. Give them with answer, then stop. If you are truly stuck, or the game says you have used all your \
commands, give the same notes with
  {play} end '...'
and stop.
"""

COMMANDS_RECORD = """  {play} 'look'                     where you are, who and what is here, the doors, the quest markers
  {play} 'journal'                  your journal entries, objectives, what each marker points at, what you carry
  {play} 'go <place | person | thing | marker N>'   travel there (no need to walk the way)
  {play} 'talk <person>'            start a conversation: the topics you can pick
  {play} 'say <topic or its number>'   pick a topic while talking; add pass or fail when the game asks for a check
  {play} 'take <thing>'   {play} 'use <thing or door>'   {play} 'read <thing>'
  {play} 'fight <who> win|lose'     you choose how a fight ends (losing means you load your last save)
  {play} 'pick <lock> win|fail'   {play} 'pickpocket <person> win|fail'
  {play} 'choose <button label or number>'   pick a button when a message box offers choices
  {play} 'name <your name>'         answer when the game asks your name"""

COMMANDS_FORMS = """  {play} 'look'                     where you are, who and what is near you, the doors
  {play} 'journal'                  your quests: journal entries and active objectives
  {play} 'magic'                    the spells and powers you have learned on your travels
  {play} 'map'                      your position, each quest marker (where, how far, which way, what it marks)
  {play} 'go <marker N | person | thing | place>'   travel there (no need to walk the way)
  {play} 'talk <person>'            start a conversation: their greeting and the topics you can pick
  {play} 'say <topic, answer or its number>'      pick a topic or an answer while talking
  {play} 'take <thing>'   {play} 'use <thing or door>'   {play} 'wait'
  {play} 'fight <who> win|lose|flee'    you choose how a fight ends (losing means you load your last save)
  {play} 'pick <lock> win|fail'   {play} 'pickpocket <person>'"""


know_text = S.know_text


def agent_settings(path: Path = AGENT) -> tuple[str, str | None]:
    """The paper player's model and effort, from its agent file's frontmatter."""
    text = Path(path).read_text(encoding="utf-8")
    head = text.split("---", 2)[1] if text.startswith("---") else ""
    kv = dict((k.strip(), v.strip()) for k, _, v in (ln.partition(":") for ln in head.splitlines()) if _)
    if not kv.get("model"):
        raise SystemExit(f"{path}: no model in its frontmatter")
    return kv["model"], kv.get("effort")


def steer_text(way: str | None = None, choose: str | None = None) -> str:
    out = ""
    if way:
        out += f" The game expects a character of your build to favour this way through where there is a choice: {way}."
    if choose:
        out += f" Where the quest offers a choice of how it ends, you mean to take this one: {choose}."
    return out


def brief(play: str, know: str, mode: str = "forms", way: str | None = None, choose: str | None = None) -> str:
    cmds = (COMMANDS_RECORD if mode == "record" else COMMANDS_FORMS).format(play=play)
    return BRIEF.format(play=play, commands=cmds, steer=steer_text(way, choose),
                        know=(f"What you already know: {know}\n") if know else "You know nothing else about this game.")


def wrapper_argv(argv: list[str], sess: str, py: str | None = None) -> list[str]:
    """The command the `play` wrapper runs for the player's arguments: the words before --think are the one
    command (`play 'answer' '1. ...'` and `play 'answer 1. ...'` alike), each kept a literal argument."""
    py = py or sys.executable
    think, pos, i = None, [], 0
    while i < len(argv):
        if argv[i] == "--think" and i + 1 < len(argv):
            think, i = argv[i + 1], i + 2
            continue
        if argv[i].startswith("--think="):
            think, i = argv[i][8:], i + 1
            continue
        pos.append(argv[i])
        i += 1
    cmd = " ".join(pos).strip()
    if cmd.split(" ", 1)[0] == "end":
        notes = cmd[3:].strip()
        for flag in ("--notes", "--take"):
            if notes.startswith(flag):
                notes = notes[len(flag):].strip()
        if len(notes) > 1 and notes[0] == notes[-1] and notes[0] in "'\"":
            notes = notes[1:-1]
        return [py, "-m", "tools.playtest", "end", sess, "--notes", notes]
    return [py, "-m", "tools.playtest", "do", sess, cmd] + (["--think", think] if think is not None else [])


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


def claude_cmd(play: Path, system: str, model: str, prompt: str, effort: str | None = None) -> list[str]:
    return ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
            *(["--effort", effort] if effort else []),
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


def run(forms, know: str | None = None, names=(), at=None, start=None, source="designed", sheet=None,
        max_commands=60, use_db=True, root: Path = S.RUNS, after=()) -> Path:
    """A form-based run (moments 2 and 3): the paper player plays the compiled forms."""
    model, effort = agent_settings()

    def make():
        folder, screen = S.new(forms, source=source, start=start, at=at, sheet=sheet, know=know, names=names,
                               use_db=use_db, max_commands=max_commands, root=root, model=model, effort=effort,
                               after=after)
        return folder, screen, brief("{play}", S.known(folder), "forms")
    return _play(make, model, effort, S)


def run_record(path, know: str | None = None, way: str | None = None, choose: str | None = None,
               max_commands=60, root: Path = S.RUNS) -> Path:
    """A record run (moment 1): the paper player plays the record's YAML view."""
    from tools.playtest import record as R
    model, effort = agent_settings()

    def make():
        folder, screen = R.new(path, root=root, know=know, way=way, choose=choose, model=model, effort=effort,
                               max_commands=max_commands)
        sess = json.loads((folder / "session.json").read_text(encoding="utf-8"))
        return folder, screen, brief("{play}", sess.get("know_text") or "", "record", way, choose)
    return _play(make, model, effort, R)


def _play(make, model, effort, mod) -> Path:
    for i in range(ATTEMPTS):
        folder, played = _attempt(make, model, effort, mod)
        if played or i == ATTEMPTS - 1:
            break
        shutil.rmtree(folder, ignore_errors=True)      # refused before its first command: nothing to keep
    return folder                                      # the last refused attempt stays, its run.json saying why


def _attempt(make, model, effort, mod):
    folder, screen, system = make()
    play = wrapper(folder)
    room = Path(tempfile.mkdtemp(prefix="pt-"))
    system = system.replace("{play}", str(play))
    prompt = f"Your game has just begun. This is what you see:\n\n{screen}\n\nPlay."
    (folder / "brief.md").write_text(system.replace(str(play), "play") + "\n---\n" + prompt + "\n", encoding="utf-8")
    t0 = time.time()
    res = run_claude(claude_cmd(play, system, model, prompt, effort), folder / "stream.jsonl", room)
    usage = res.get("usage") or {}
    text = str(res.get("result") or "")
    err = text if res.get("stopped") == "error" else None
    run = mod.write_run(folder, {"player_error": err, "stopped": res.get("stopped"), "subtype": res.get("subtype"),
                                 "model": model, "effort": effort,
                                 "cost_usd": res.get("total_cost_usd"), "minutes": round((time.time() - t0) / 60, 1),
                                 "turns": res.get("num_turns"), "tokens": {k: usage.get(k) for k in (
                                     "input_tokens", "output_tokens", "cache_read_input_tokens",
                                     "cache_creation_input_tokens")}})
    played = len(run["commands_used"]) if "commands_used" in run else run["counts"]["commands"]
    if mod is S and played and not S.has_notes(folder):
        costs = []
        ask_questions(folder, system, model, room, cost=costs, effort=effort)
        run = S.write_run(folder, {"cost_usd": round((res.get("total_cost_usd") or 0) + sum(costs), 6)})
    shutil.rmtree(room, ignore_errors=True)
    shutil.rmtree(play.parent, ignore_errors=True)
    return folder, played > 0


def questions_prompt(folder: Path) -> str:
    """The closing turn of a run that stopped without notes: what the player did and thought, then the questions on
    what they understood, numbered."""
    rows = [r for r in S.transcript(folder) if r["think"] is not None and not r.get("refused")]
    played = "\n".join(f"> {r['command']}\n  (you thought: {r['think']})" for r in rows)
    return ("You have stopped playing. This is what you did:\n\n" + played + "\n\nNow answer these short "
            "questions, each by its number, in one reply, in your own words, from what the game showed you.\n\n" +
            S.numbered_questions())


def ask_questions(folder: Path, system: str, model: str, room: Path, ask=None, cost: list | None = None,
                  effort: str | None = None) -> str:
    """Ask the closing questions as a separate final turn, and store whatever comes back."""
    prompt = questions_prompt(folder)
    if ask is None:
        def ask(p):
            cmd = ["claude", "-p", p, "--output-format", "stream-json", "--verbose", "--model", model,
                   *(["--effort", effort] if effort else []),
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

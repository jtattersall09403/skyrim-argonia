"""B01 personification in the dialogue linter: an inanimate subject doing a person's act is flagged, plain facts are not."""
import importlib.util
import pathlib
import re

import yaml

SKILL = pathlib.Path(__file__).resolve().parents[2] / ".claude" / "skills" / "dialogue-write"
spec = importlib.util.spec_from_file_location("dialogue_lint", SKILL / "lint.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)
B01 = next(b for b in yaml.safe_load((SKILL / "bans.yaml").read_text()) if b["id"] == "B01-personification")
RX = re.compile(lint.pattern(B01))

FLAGGED = [
    "The roll adds more months for food.",
    "The hold heard you.",
    "Whoever is left inside, the fire takes.",
    "The village would say otherwise.",
    "The tally book keeps every name.",
    "The town has not trusted us since.",
    "The marsh is watching you.",
    "Hereguard's ledger says you owe ten months.",
    "The lodge talks of salt.",
]
CLEAN = [
    "The overseer adds months for food on the roll.",
    "They heard you in the hold.",
    "The ledger is kept in the chest.",
    "The roll burned in the fire.",
    "Ussa-Rekh keeps our carved tokens in the chest.",
    "The roll is called at dawn.",
]


def test_flags_inanimate_subject_doing_a_persons_act():
    missed = [s for s in FLAGGED if not RX.search(s)]
    assert not missed, missed


def test_leaves_people_passives_and_plain_facts():
    noisy = [s for s in CLEAN if RX.search(s)]
    assert not noisy, noisy

"""talk_check's replies-versus-facts check: a reply names only what its speaker's facts and row back."""
from tools.argonia_world.talk_check import unbacked

BACKING = ("Lilmoth Dock lies about 365 m east of here. A gleamblossom grows about 60 m south of here. "
           "Thinks Lifts-The-Sacks loads well; guards the south side of the plantation")


def test_backed_reply_is_clean():
    assert unbacked("The dock is east. Gleamblossom grows south. Lifts-The-Sacks loads well.", BACKING) == []


def test_unknown_name_is_caught():
    assert unbacked("Ask for Rakhee-Tul at the dock.", BACKING) == ["Rakhee-Tul"]


def test_sentence_initial_word_is_not_a_name():
    assert unbacked("Halt. Mind the water. Ha.", BACKING) == []


def test_ingredient_not_in_facts_is_caught():
    assert unbacked("Nightshade grows near the dock.", BACKING) == ["nightshade"]


def test_side_not_in_row_is_caught():
    assert unbacked("They stand on the north side.", BACKING) == ["north side"]
    assert unbacked("They stand on the south side.", BACKING) == []

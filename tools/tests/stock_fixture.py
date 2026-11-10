"""A small stocked place for the stock build and check tests: one household's chest, one loose scroll, one guard,
one trader; the read-back of a build that matches its rows (tools/places/stock/verify.py's `load` shape)."""
GOLD = "Skyrim.esm:00000F"
DAGGER, SWORD, RING, SCROLL, APPLE, EBONY, NORD = ("Skyrim.esm:01397E", "Skyrim.esm:013989", "Skyrim.esm:03B97C",
                                                   "Skyrim.esm:0F1234", "Skyrim.esm:064B31", "Skyrim.esm:0139B1",
                                                   "Skyrim.esm:0B3C02")
P = "ArgoniaNWPlaces.esp"


def items() -> dict:
    def it(edid, kind, value, tier, sig=True, never=False):
        rec = {"weapon": "WEAP", "jewellery": "ARMO", "scroll": "SCRL", "food": "ALCH", "gold": "MISC"}[kind]
        return {"known": True, "significant": sig, "value": value, "tier": tier, "kind": kind, "edid": edid, "name": edid,
                "never": never, "sig": rec}
    return {GOLD: it("Gold001", "gold", 1, "T1"), DAGGER: it("IronDagger", "weapon", 10, "T1"),
            SWORD: it("SteelSword", "weapon", 45, "T2"), RING: it("JewelryRingSilver", "jewellery", 30, "T1"),
            SCROLL: it("CandlelightScroll", "scroll", 25, "T1"), APPLE: it("FoodApple", "food", 3, "T1", sig=False),
            EBONY: it("EbonySword", "weapon", 720, "T5"), NORD: it("NordHeroSword", "weapon", 100, "T2", never=True)}


def stock() -> dict:
    tiers = ["T1", "T2", "T3", "T4", "T5", "T6"]
    return {
        "pid": "t", "items": items(), "mine": set(),
        "tier_rank": {t: i + 1 for i, t in enumerate(tiers)},
        "value_max": {"T1": 80, "T2": 250, "T3": 700, "T4": 1600, "T5": 3500, "T6": 100000},
        "open": "T1", "ceiling": "T3", "locks": {"Novice": 1, "Apprentice": 25, "Adept": 50},
        "sec_rank": {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "S4": 4, "S5": 5},
        "share": {"W1": 0.1, "W2": 0.25, "W3": 0.5, "W4": 0.75, "W5": 1.0, "none": 1.0, "faction": 1.0},
        "bands": {"W2": {"carried": [2, 10], "top_tier": "T1", "jewellery": 0},
                  "W3": {"carried": [8, 25], "top_tier": "T2", "jewellery": 1}},
        "issue_tier": "T2", "caps": {"unique": 40, "T6": 60},
        "containers": [{"ref": "X.esm:000009", "space": "house", "owner_person": None, "owner_household": "t.household.house",
                        "owner_faction": None, "lock": None, "security": "S1", "tier": "T2", "gold": 30,
                        "items": [(RING, 1)]}],
        "loose": [{"id": "X.esm:00000A", "space": "house", "item": SCROLL, "count": 1, "owner_person": None,
                   "owner_faction": "t.household.house"}],
        "persons": {"t.head": {"band": "W3", "household": "t.household.house", "role": "merchant", "name": "Head"},
                    "t.guard": {"band": "W2", "household": "t.household.house", "role": "guard", "name": "Guard"}},
        "person_items": {"t.head": [(DAGGER, 1, True), (GOLD, 12, False), (RING, 1, True)],
                         "t.guard": [(SWORD, 1, True), (GOLD, 5, False)]},
        "traders": {"t.head": {"gold": 500, "items": [(DAGGER, 3)]}},
        "deliveries": [{"give_seq": 0, "kind": "fishing", "detail": "T", "status": "delivered", "by": "record",
                        "person": None, "ref": None, "why": "the river by the place"},
                       {"give_seq": 1, "kind": "trader-general", "detail": "a trader", "status": "delivered", "by": "person",
                        "person": "t.head", "ref": None, "why": "Head gives it"}],
        "unique": [],
        "built": {
            "containers": {("house", "X.esm:000009"): {"fk": f"{P}:010001", "contents": [(APPLE, 2), (RING, 1), (GOLD, 30)],
                                                       "respawns": False, "lock": None, "owner": f"{P}:010050"}},
            "loose": {("house", "X.esm:00000A"): {"fk": f"{P}:010002", "item": SCROLL, "count": 1, "owner": f"{P}:010050"}},
            "npcs": {"t.head": {"fk": f"{P}:010010", "inventory": [(GOLD, 12), (DAGGER, 1)], "outfit_items": [RING],
                                "death_item": "", "faction_keys": [f"{P}:010050"]},
                     "t.guard": {"fk": f"{P}:010011", "inventory": [(GOLD, 5), (APPLE, 1), (SWORD, 1)],
                                 "outfit_items": [], "death_item": "", "faction_keys": [f"{P}:010050"]}},
            "chests": {"t.head": {"contents": [(DAGGER, 3), (GOLD, 500)], "respawns": True}},
        },
        "owner_fk": {"person:t.head": f"{P}:010010", "person:t.guard": f"{P}:010011",
                     "household:t.household.house": f"{P}:010050"},
        "world_markers": {"ANW_MapMarker_t"},
    }

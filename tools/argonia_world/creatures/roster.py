"""The authored half of the creature data (1.15 §g.2-3): which mod form stands for which creature kind, which region
classes each kind lives in, its medium, its den, the band afflictions and the no-spawn radii. `creatures seed`
writes these into the world database (the database is the home; this module is the seed, as vegetation/lists.py).

Lore: the lore dossier topics/fauna-hazards.md (FH), the lore dossier topics/loading-facts.md (LF, by fact
id), docs/design/world/74-ecology.md (the creature table and its placement rules). Region classes are the
suffixes of land_region.id (regions/classify.py).
"""
from __future__ import annotations

FH = "lore dossier topics/fauna-hazards.md"
LF = "lore dossier topics/loading-facts.md"
ECO = "docs/design/world/74-ecology.md"

KOTM, CIP, BM, BIRDS = ("King of the Murkmire.esp", "Here There Be Monsters - Curse of Cipactli.esp",
                        "Black Marsh.esm", "Tropical Skyrim -- Birds.esp")

# the region classes and what about each one draws a creature (land_region suffixes; 'border' is the map edge)
CLASSES = {
    "coastal-lagoon": "sea and brackish shallows behind the mangrove wall",
    "tidal-delta": "tidal channels and mudflats where the rivers meet the sea",
    "deep-sink-basin": "deep standing blackwater over sunken ground",
    "interior-swamp": "standing fresh and black water among reedbeds",
    "flooded-forest": "forest standing in shallow water",
    "rootland": "the Hist root forest floor, mostly dry",
    "deep-river-corridor": "deep rivers and their banks",
    "western-frontier": "the drier western upland toward Cyrodiil",
    "northern-transition": "the firmer northern ground toward Morrowind",
}
ALL = tuple(CLASSES)
WET = ("coastal-lagoon", "tidal-delta", "deep-sink-basin", "interior-swamp", "flooded-forest", "deep-river-corridor")

# New creature kinds the mods bring that the lore names (rows added to `creature` by seed, with a why).
NEW = {
    "creature.singing-frog": dict(name="Singing Frog", kind="fauna", hostility="neutral", bands=("D1",),
        ground="pond margins, reed roots", water="still shallows", day="crepuscular", group=(2, 6),
        why="Singing frogs live near the Panther River; musicians prize their calls (LF fact.singing-frogs).",
        notes="A small frog whose chirp carries over the water at dusk."),
    "creature.dragon-frog": dict(name="Dragon Frog", kind="fauna", hostility="guarded", bands=("D1", "D2"),
        ground="leaf litter, warm pools", water="still shallows", day="diurnal", group=(1, 3),
        why="Black Marsh dragon frogs have small wings and spew a poisonous gas (LF fact.dragon-frog-poison-breath).",
        notes="A mottled frog with stub wings; its breath sickens what comes close."),
    "creature.burglar-crab": dict(name="Burglar Crab", kind="fauna", hostility="guarded", bands=("D1", "D2"),
        ground="mud banks, tide lines", water="shallows", day="always", group=(1, 4),
        why="Burglar crabs eat snails and smaller crabs, then move into the shells (LF, Tribes of Murkmire: Root-House People).",
        notes="A shell-stealing crab of the banks and tide lines."),
    "creature.marsh-turtle": dict(name="Marsh Turtle", kind="fauna", hostility="neutral", bands=("D1",),
        ground="sunning logs, sand banks", water="slow shallows", day="diurnal", group=(1, 3),
        why="The Bright-Throat tribe hold the turtle as a totem; turtle shells make platters (LF fact.bright-throat-turtle).",
        notes="A slow river turtle; its shell is a platter in every hearth-house."),
    "creature.giant-centipede": dict(name="Giant Centipede", kind="predator", hostility="hostile", bands=("D2", "D3"),
        ground="rotting logs, root hollows", water="none", day="nocturnal", group=(1, 2),
        why="Centipedes are part of Argonian life (LF fact.centipede-pillows); the Murkmire mods ship giant ones.",
        notes="A man-long centipede of the root hollows; its bite numbs."),
    "creature.giant-snail": dict(name="Giant Snail", kind="fauna", hostility="neutral", bands=("D1",),
        ground="wet stone, rotting wood", water="none", day="nocturnal", group=(1, 3),
        why="Murkmire chefs cook with snail slime (LF, Argonian Cuisine); King of the Murkmire's own snails.",
        notes="A grazing snail the size of a dog."),
    "creature.marsh-bird": dict(name="Marsh Bird", kind="fauna", hostility="neutral", bands=("D1",),
        ground="banks, mudflats, snags", water="wades", day="diurnal", group=(2, 8),
        why="Marsh giants boost bird diversity (FH, Marsh Giant); shore and water birds of the coast and rivers.",
        notes="Kingfishers, sandpipers, oystercatchers and gulls: the province's ambient birdlife."),
}

# creature -> (medium, [(plugin, edid)], classes, den)
R = {
    "creature.alit": ("land", [(KOTM, "ALPAAlit01")], ("western-frontier", "northern-transition"), True),
    "creature.bog-blight": ("shore", [(CIP, "CIPHTBMBogBlight"), (CIP, "CIPHTBMBogBlightF")],
                            ("deep-sink-basin", "interior-swamp", "flooded-forest", "rootland"), True),
    "creature.bog-dog": ("land", [(BM, "0wolfdrake")],
                         ("western-frontier", "rootland", "northern-transition", "flooded-forest"), False),
    "creature.crocodile": ("shore", [(KOTM, "EncCrocodileBlackMarsh01"), (KOTM, "EncCrocodileBlackMarsh02"),
                                     (CIP, "CIPHTBMCrocodile"), (CIP, "CIPHTBMCrocodileSalt")],
                           WET + ("western-frontier",), True),
    "creature.crow": ("land", [(BIRDS, "01BOSCrow1"), (BIRDS, "01BOSGreycrow"), (BIRDS, "01BOSActorRaven")], ALL, False),
    "creature.death-hopper": ("shore", [(KOTM, "FrogGreen01Giant"), (KOTM, "FrogRed01Giant"),
                                        (KOTM, "FrogBrown01Giant"), (KOTM, "FrogBlue01Giant")],
                              ("interior-swamp", "flooded-forest", "rootland", "western-frontier", "deep-sink-basin"), False),
    "creature.dreugh": ("water", [(BM, "SoM_I5K0Dreugh")], ("coastal-lagoon", "tidal-delta"), True),
    "creature.fellrunner": ("land", [(CIP, "CIPHTBMGallimimus"), (CIP, "CIPHTBMMudRunner")],
                            ("rootland", "western-frontier", "northern-transition", "tidal-delta"), False),
    "creature.fleshfly": ("land", [(CIP, "CIPHTBMBloodFlies")], ALL, False),
    "creature.giant-leech": ("water", [(BM, "Leech"), (BM, "0GiantLeech")],
                             ("interior-swamp", "deep-sink-basin", "flooded-forest", "deep-river-corridor",
                              "tidal-delta", "rootland"), False),
    "creature.giant-wasp": ("land", [(CIP, "CIPHTBMMosquito")],
                            ("rootland", "western-frontier", "northern-transition", "flooded-forest"), True),
    "creature.hackwing": ("land", [(CIP, "CIPHTBMHackwing"), (CIP, "CIPHTBMHackwing2")],
                          ("tidal-delta", "coastal-lagoon", "interior-swamp", "western-frontier",
                           "northern-transition"), True),
    "creature.haj-mota": ("shore", [(BM, "Turtle")],
                          ("tidal-delta", "deep-river-corridor", "coastal-lagoon", "interior-swamp"), True),
    "creature.hoarvor": ("land", [(BM, "0Forestspider")],
                         ("rootland", "western-frontier", "northern-transition", "deep-sink-basin"), False),
    "creature.jassa-red-slug": ("land", [(KOTM, "ArgoniaEncSnail01"), (KOTM, "ArgoniaEncSnail02")],
                                ("flooded-forest", "rootland", "interior-swamp", "deep-sink-basin",
                                 "deep-river-corridor"), False),
    "creature.kaj-thux": ("shore", [(KOTM, "GiantSnakeGreen01"), (KOTM, "GiantSnakeBrown01"),
                                    (KOTM, "GiantSnakeRed01"), (KOTM, "GiantSnakeBlue01")],
                          ("deep-river-corridor", "flooded-forest", "interior-swamp", "deep-sink-basin", "rootland"), True),
    "creature.kotu-gava": ("shore", [(KOTM, "KotuGava01"), (KOTM, "KotuGava02"), (KOTM, "KotuGava01Large"),
                                     (KOTM, "KotuGava02Large")],
                           ("interior-swamp", "flooded-forest", "deep-sink-basin", "rootland", "deep-river-corridor",
                            "tidal-delta"), False),
    "creature.marsh-giant": ("land", [(BM, "0AncientTree")], ("rootland", "flooded-forest"), True),
    "creature.marsh-rat": ("land", [(CIP, "CIPHTBMSwampRat")], ALL, False),
    "creature.miregaunt": ("shore", [(CIP, "CIPHTBMMireGaunt")], ("deep-sink-basin", "flooded-forest", "rootland"), True),
    "creature.moon-adder": ("land", [(CIP, "CIPHTBMSnake1"), (CIP, "CIPHTBMSnake2")],
                            ("rootland", "western-frontier", "northern-transition", "interior-swamp",
                             "flooded-forest"), False),
    "creature.sea-drake": ("water", [(CIP, "CIPHTBMSeaDrake")], ("coastal-lagoon",), True),
    "creature.slaughterfish": ("water", [(KOTM, "EncSlaughterfishBlackMarsh")],
                               ("coastal-lagoon", "tidal-delta", "deep-river-corridor", "interior-swamp",
                                "deep-sink-basin"), False),
    "creature.swamp-jelly": ("water", [(CIP, "CIPHTBMSwampJellyBetty"), (CIP, "CIPHTBMSwampJellyBull"),
                                       (CIP, "CIPHTBMSwampJellyCalf")],
                             ("interior-swamp", "deep-sink-basin", "flooded-forest", "tidal-delta"), False),
    "creature.voriplasm": ("shore", [(KOTM, "Voriplasm01"), (KOTM, "Voriplasm02"), (KOTM, "Voriplasm03")],
                           ("deep-sink-basin", "flooded-forest", "interior-swamp"), False),
    "creature.wamasu": ("shore", [(KOTM, "Wamasu01"), (CIP, "CIPHTBMWamasu")],
                        ("deep-sink-basin", "rootland", "flooded-forest", "interior-swamp"), True),
    "creature.wisp": ("shore", [(BM, "RestlessDead")], ("deep-sink-basin", "interior-swamp", "flooded-forest"), False),
    "creature.singing-frog": ("shore", [(KOTM, "FrogGreen01"), (KOTM, "FrogBlue01"), (CIP, "CIPHTBMFrogGreen"),
                                        (CIP, "CIPHTBMFrogBlue")],
                              ("deep-river-corridor", "interior-swamp", "flooded-forest", "rootland", "tidal-delta",
                               "western-frontier", "northern-transition"), False),
    "creature.dragon-frog": ("shore", [(KOTM, "FrogRed01"), (KOTM, "FrogBrown01"), (CIP, "CIPHTBMFrogRed")],
                             ("flooded-forest", "rootland", "interior-swamp", "deep-sink-basin"), False),
    "creature.burglar-crab": ("shore", [(KOTM, "EncMudcrabMediumBlackMarsh"), (KOTM, "EncMudcrabLargeBlackMarsh"),
                                        (KOTM, "EncMudcrabGiantBlackMarsh")],
                              ("coastal-lagoon", "tidal-delta", "deep-river-corridor", "deep-sink-basin"), False),
    "creature.marsh-turtle": ("shore", [(CIP, "CIPHTBMTurtleFemale"), (CIP, "CIPHTBMTurtleMale"),
                                        (CIP, "CIPHTBMTurtleYoung")],
                              ("tidal-delta", "coastal-lagoon", "deep-river-corridor", "interior-swamp",
                               "flooded-forest"), False),
    "creature.giant-centipede": ("land", [(CIP, "CIPHTBMCentipede"), (KOTM, "GiantCentipede01")],
                                 ("rootland", "flooded-forest", "western-frontier", "northern-transition",
                                  "deep-sink-basin"), False),
    "creature.giant-snail": ("land", [(KOTM, "ArgoniaEncLargeSnail01"), (KOTM, "ArgoniaEncLargeSnail02"),
                                      (KOTM, "ArgoniaEncGiantSnail02")],
                             ("flooded-forest", "interior-swamp", "rootland", "deep-sink-basin",
                              "deep-river-corridor"), False),
    "creature.marsh-bird": ("shore", [(BIRDS, "01BOSActorKingfisher"), (BIRDS, "01BOSPectoralSandpiper"),
                                      (BIRDS, "01BOSOystercatcher"), (BIRDS, "01BOSActorSeagull")], ALL, False),
}
# kinds with no NPC_ in any pinned mod (vanilla critters or hand-authored): left out of the lists, named here
NO_FORM = {
    "creature.osheeja-gar": "a fish critter (vanilla ambient fish), not an actor: the water lane's critters, owed",
    "creature.torchbug": "a firefly critter (ACTI), not an actor: placed with the vegetation, owed",
    "creature.medusa": "Murkwood ruins only (FH): placed by the place record, not the wild lists",
}

# medium rules: (min_depth, max_depth, shore_above, max_slope)
MEDIUM = {"water": (0.6, 60.0, 0.0, 90.0), "shore": (-1.0, 1.2, 4.0, 30.0), "land": (-99.0, 0.0, 99.0, 35.0)}
DEEP = {"creature.sea-drake": 3.0, "creature.dreugh": 2.0}  # min depth for the deep-water kinds (FH: deep water)

# band -> (actor level, spawn points per cell): the levels from danger_band_combat (76 §128); the counts from
# Skyrim.esm's creature refs per cell of wilderness (vanilla/creatures.py: shore 1.05, forest 0.96, open 0.26,
# water 0.09), falling with the band as 74-ecology rule 1 asks (the hunters are rare)
BANDS = {"D1": 1.0, "D2": 0.8, "D3": 0.6, "D4": 0.4, "D5": 0.2}

# place class -> no-spawn radius (74-ecology rule 3: nothing wild inside a settlement)
NO_SPAWN = {
    "settlement": (150.0, "74-ecology rule 3: no wild creature inside a settlement's boundary"),
    "civic": (120.0, "a civic place is inside or beside a settlement"),
    "works": (90.0, "worked ground: people at work, kept animals only"),
    "martial": (110.0, "a fort's guarded ground"),
    "transit": (60.0, "a ferry stage, relay or toll: people wait there"),
    "camp": (60.0, "a camp's fire and sleepers"),
    "sacred": (60.0, "a shrine's tended ground"),
    "lone": (40.0, "a hermit's hut or lone house"),
    "ruin": (25.0, "the ruin's own residents are placed by its record"),
    "lair": (25.0, "the lair's own residents are placed by its record (den sockets)"),
}

AFFLICTIONS = {
    "disease.swamp-rot": ("disease", "Swamp Rot", "health regenerates slowly", "FH Diseases: killed a Maran mission in a month"),
    "disease.blood-rot": ("disease", "Blood Rot", "stamina regenerates slowly", "FH Diseases"),
    "disease.the-droops": ("disease", "The Droops", "carry weight lowered", "FH Diseases"),
    "disease.swamp-fever": ("disease", "Swamp Fever", "magicka lowered", "FH Diseases"),
    "disease.rust-chancre": ("disease", "Rust Chancre", "armour lowered", "FH Diseases"),
    "disease.greenspore": ("disease", "Greenspore", "health lowered", "FH Diseases"),
    "poison.adder-venom": ("poison", "Adder Venom", "damage health over time", "74-ecology moon-adder"),
    "poison.wasp-sting": ("poison", "Wasp Sting", "damage stamina over time", "FH: giant wasps the size of ponies"),
    "poison.frog-breath": ("poison", "Dragon-Frog Breath", "damage health, slows", "LF fact.dragon-frog-poison-breath"),
    "poison.voriplasm-acid": ("poison", "Voriplasm Acid", "damage health and armour", "FH Voriplasm: strips to the bone"),
    "poison.centipede-numb": ("poison", "Centipede Numbing", "slows", "the mods' giant centipede bite"),
}
# (band, creature, affliction, carrier, chance, why)
EFFECTS = [
    ("D1", "creature.marsh-rat", "disease.blood-rot", "bite", 0.1, "rats in carcasses (FH Everyday hazards)"),
    ("D1", "creature.giant-leech", "disease.swamp-fever", "bite", 0.1, "leeches of the seeps (FH)"),
    ("D2", "creature.giant-leech", "disease.swamp-fever", "bite", 0.2, "leeches of the seeps (FH)"),
    ("D1", "creature.fleshfly", "disease.swamp-rot", "bite", 0.1, "fleshflies eat flesh (FH Everyday hazards)"),
    ("D2", "creature.fleshfly", "disease.swamp-rot", "bite", 0.2, "fleshflies eat flesh (FH Everyday hazards)"),
    ("D3", "creature.fleshfly", "disease.swamp-rot", "bite", 0.3, "fleshflies eat flesh (FH Everyday hazards)"),
    ("D2", "creature.bog-dog", "disease.rust-chancre", "bite", 0.15, "a scavenger's bite"),
    ("D2", "creature.bog-blight", "disease.greenspore", "touch", 0.25, "a drowned corpse's rot"),
    ("D3", "creature.bog-blight", "disease.greenspore", "touch", 0.35, "a drowned corpse's rot"),
    ("D2", "creature.crocodile", "disease.the-droops", "bite", 0.15, "carrion-fouled jaws"),
    ("D3", "creature.crocodile", "disease.the-droops", "bite", 0.25, "carrion-fouled jaws"),
    ("D1", "creature.moon-adder", "poison.adder-venom", "bite", 0.5, "an adder"),
    ("D2", "creature.moon-adder", "poison.adder-venom", "bite", 0.7, "an adder"),
    ("D2", "creature.giant-wasp", "poison.wasp-sting", "sting", 0.6, "FH: giant wasps"),
    ("D3", "creature.giant-wasp", "poison.wasp-sting", "sting", 0.8, "FH: giant wasps"),
    ("D1", "creature.dragon-frog", "poison.frog-breath", "breath", 0.5, "LF fact.dragon-frog-poison-breath"),
    ("D2", "creature.dragon-frog", "poison.frog-breath", "breath", 0.7, "LF fact.dragon-frog-poison-breath"),
    ("D3", "creature.voriplasm", "poison.voriplasm-acid", "touch", 1.0, "FH Voriplasm"),
    ("D4", "creature.voriplasm", "poison.voriplasm-acid", "touch", 1.0, "FH Voriplasm"),
    ("D2", "creature.giant-centipede", "poison.centipede-numb", "bite", 0.5, "the mods' centipede"),
    ("D3", "creature.giant-centipede", "poison.centipede-numb", "bite", 0.7, "the mods' centipede"),
]

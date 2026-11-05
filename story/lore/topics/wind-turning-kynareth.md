# Turning the wind: a sailor's call to Kynareth

Status: `CANON_EXPLICIT` for Kynareth, her sailors and her storms, the Argonian and Kothringi sea trade; the Kyne priestess who reads the winds; `EXTRAPOLATED` for the slice's form, a lesser power that turns the wind. No sourced spell, power or item turns the wind at sea. Era policy: [0002](../../../../docs/decisions/0002-era-and-source-confidence.md). The Kynareth and sea-trade facts hold in 4E 201. The Kothringi are history: the Knahaten Flu of 2E 560 ended them. The Kyne priestess is ESO (2E), so she is a precedent for the practice and says nothing about who holds power now.

Sources, fetched 2026-10-24 through the UESP API: Lore:Kynareth, Lore:Kyne, Lore:Sea Transportation and Skyrim:Clear Skies (`prop=extracts`); Lore:Kothringi, Online:The Winds of Kyne and Online:Priestess Hodyette (`action=parse`, wikitext). Searched with no hit for a spell or item that commands the wind: Lore:Alteration (no wind effect), the vault extract `uesp_morrowind_blackmarsh_extract.jsonl.xz` (6,299 pages; a regex for command, control or call the wind, fair wind, weather magic and wind to fill the sails found only Jurgen Windcaller, a Nord Tongue). `list=search` on the API returned no hits for any query on 2026-10-24, so pages were fetched by title.

## What the lore gives

- `CANON_EXPLICIT`: Kynareth "is the goddess of the heavens, the winds, the sea, the elements" and "the unseen spirits of the air", "Patron of sailors and travelers" (Lore:Kynareth).
- `CANON_EXPLICIT`: Among Redguards she is "very popular", "particularly among sailors. Shrines of her can be found across most port cities" (Lore:Kynareth, Redguard). In Gonfalon Bay she is "the patron of sailors and fisherfolk" (Lore:Kynareth, Breton).
- `CANON_EXPLICIT`: As Kyne, "the goddess of the Storm, she is strongly associated with wind and rain; is thought to control both forces" (Lore:Kyne).
- `CANON_EXPLICIT`: The Ring of the Wind, "a legendary artifact associated with Kynareth, the Goddess of the Winds", grants great speed. A sapphire tied to her "possesses the ability to influence the weather" (Lore:Kynareth, artifacts).
- `CANON_EXPLICIT`: Argonians are "heavily present among the crews of big ships" but rarely build them, sailing "other races' ships", "commonly those of the Dunmer or the Imperial". "Argonian captains are famous as pirates, privateers and smugglers; and both coastal and inland port cities of Black Marsh have a long tradition of sea sailing" (Lore:Sea Transportation).
- `CANON_EXPLICIT`, history in our era: The Kothringi of Black Marsh were "avid sailors". One of their vessels had "unusual paddle placement, shallow draft" and "a sail". They worshipped Kynareth "alongside Mara and Dibella" (Lore:Kothringi).
- `CANON_EXPLICIT`, 2E: Priestess Hodyette reads the weather for a Murkmire expedition: "Kyne's the Goddess of the Storm", "From the wind of your lungs, invoke her power to view the winds of the world"; "Kyne needs to be called upon if she's to give her blessing. A hearty shout is usually good enough" (Online:Priestess Hodyette; Online:The Winds of Kyne, quest giver Jee-Lar of Stormhold).
- `CANON_EXPLICIT`: Skyrim's Clear Skies is a dragon shout that clears weather anywhere in Skyrim (Skyrim:Clear Skies). A voice turning the weather is attested in our era. The Thu'um is a Nord art, so we take the precedent and not the shout.

## The slice's form

- **A lesser power, not a spell or an item.** `EXTRAPOLATED`. It is used often, so it must cost nothing per use. A lesser power has no magicka cost and no daily limit. A spell would tax magicka on every turn of the wind; an item can be lost or sold. The lore grounds a prayer to a goddess of winds better than a school effect: Alteration has no wind effect (Lore:Alteration).
- **What it is.** A sailor's short call into the wind asking Kynareth to turn it. It is Hodyette's practice ("from the wind of your lungs") carried by the foreign crews who take Argonians on as hands. One quick action, then a pick of the direction (0159 ruling 4). It turns the weather's wind, never a private wind.
- `EXTRAPOLATED`: **Who teaches it, where.** Xal-Jei, the lighter's master at the Lighter Flotilla (`npc.mercantile-coast.lighter-flotilla.lighterman`, `world/sources/registries/npcs.json`). The Flotilla is Lilmoth's port water. Its crews "live aboard their boats at permanent moorings beside the lighter quay" and handle foreign ships. Lilmoth is the port city where a Kynareth sailors' custom would reach Argonian crews (Lore:Sea Transportation; Lore:Kynareth, port shrines). The Flotilla is also the slice's only sea-hull seller, so you learns the call where the hull that needs it is sold.
- **Why not a Hist gift or a Sithis rite.** None of the Argonian faith pages in the lore set (Lore:Hist, Lore:Sithis, `topics/sithis-nisswo-shadowscales.md`) says anything about the wind. The custom is a borrowed sailors' one and reads that way in dialogue.

## Open for the writers

- The power's in-game name and description go through `text-review`. A plain working name is "Call the Wind".

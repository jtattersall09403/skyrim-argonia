# Gap register — what the game must know that canon does not say

Packet 2 output, closed out 2026-08-24 after packets 3–7.

**Status: zero `OPEN`.** Every gap is `FILLED`, `DECIDED` (owner), or `DEFER`
with a stated reason and a phase it belongs to.

**How to read this.** Each gap has an ID, a question, what canon gives us to grip
on, and a status:

- `FILLED` — answered, with the file and section that answers it.
- `DECIDED` — owner decision of 2026-08-24 ([owner-questions.md](owner-questions.md)).
- `DEFER` — genuinely does not need a lore answer; the remaining work is
  technical or belongs to a later phase. Reason and phase given.
- `MYSTERY` — canon leaves it open on purpose and so do we.

**Rule used when filling.** The *least inventive* answer consistent with the
anchors, preferring answers that explain something we already have to build.

### Where the answers live

| File | Answers |
|---|---|
| [argonia-4e201-state.md](argonia-4e201-state.md) | Province government, cities, foreign relations, economy, routes, danger, the trauma directive (§9) |
| [settlement-register.md](settlement-register.md) | Every settlement's 4E 201 status, magnitude, currency tiers, White Rose, Fort Swampmoth, drifting villages, xanmeer states |
| [../topics/hist-placement.md](../topics/hist-placement.md) | Which Hist stands where, in what state, and who speaks for it |
| [../topics/guilds-and-orders.md](../topics/guilds-and-orders.md) | Synod, College of Whispers, Fighters/Thieves Guild, Dark Brotherhood, Cyrodilic Collections, the Wild Ones, the Conclaves |
| [../topics/ecology-encounters-loot.md](../topics/ecology-encounters-loot.md) | Encounter composition, territory-holders, loot provenance, seasonal keying |

---

## 1. Province-scale government

| ID | Question | Status |
|---|---|---|
| G1.1 | **Who governs Argonia in 4E 201?** | `DECIDED` Q1 — An-Xileel **successor state**: inherited offices, titles and name; not the mandate. → state §1 |
| G1.2 | Is there any province-wide institution at all? | `FILLED` — a **minimal state** (border force, port customs, a claim to speak abroad, almost no writ inland) plus the **great Root Talk convocation**, which is an occasion, not a government. → state §1–2 |
| G1.3 | What is the province called by its own people, and what does the state call itself? | `FILLED` — *Argonia* officially; *Black Marsh* abroad; **no Argonian word** at all, only *kronka-thatith* and the wide-swamp gesture. The state is officially "the An-Xileel", colloquially "the Archwardens / the Organism / the Wardens". → state §1 |
| G1.4 | Who commands armed force, and how much? | `FILLED` — city **shellback levies**, tribal **kaals**, and a **frontier screen** of a few hundred irregulars. No standing army, no navy. The deterrent is the guerrilla reputation and the marsh. → state §2 |
| G1.5 | Is there a legal system above the tribe? | `FILLED` — no. **Vicecanons** (magistrates) in the northern cities, **merchant councils** in the ports, chosen **arbitrators** in the villages, and the collapsing **ku-vastei** arbiter role. → state §2 |
| G1.6 | Foreign relations — embassies, treaties, recognition? | `FILLED` — none formal. Three legal entries (Blackwood Road, Tear road, the ports) and one deliberate loophole (Alten Corimont). → state §5 |
| G1.7 | Who speaks for the Hist province-wide? | `DECIDED` Q2 — **nobody standing**. The **great Root Talk at Helstrom** in Hist-Tsoko is a convocation with no executive power. → state §2, hist-placement |

## 2. The eight majors and Alten Corimont

| ID | City | Status |
|---|---|---|
| G2.1 | **Lilmoth** | `DECIDED` Q4 — rebuilt but not restored; merchant council; drowned Imperial quarter unrepaired; Pusbottom repopulated; third Hist **feared and tended** with a rotating tree-minder's post; politically hostile to the successor state. → state §4, lilmoth.md, hist-placement §4 |
| G2.2 | **Stormhold** | `FILLED` — Vicecanons; the state's working border offices; crystal trade; oldest and largest Dunmer minority; town-square Hist. → state §4 |
| G2.3 | **Gideon** | `FILLED` — civic council in the Governor's Mansion, courthouse still sitting; Lukiul-majority; rootworm terminus; Archein plantations left derelict; a **disputed Hist cutting** in the city gardens. → state §4, hist-placement |
| G2.4 | **Helstrom** | `FILLED` + `DECIDED` Q2 — an assembly of interior naheesh and tree-minders that becomes the great Root Talk in Hist-Tsoko; a tribal guard accountable to nobody outside; the state's formal seat, largely ignored by it. → state §4 |
| G2.5 | **Thorn** | `FILLED` — Vicecanon(s) and the disputed field-owners; saltrice title unresolved since Dres left; large Dunmer minority from mixed families; field-edge Hist outside the walls. → state §4 |
| G2.6 | **Archon** | `FILLED` — harbour authority in the EEC's old buildings; the province's principal legal port; the letters-of-marque tradition substitutes for a navy; Shadowscale facility sealed and watched. → state §4 |
| G2.7 | **Soulrest** | `FILLED` — genuinely contested (merchant council, orphaned Imperial apparatus, the tribes who burned the mines, the river interests); gold and timber workings still derelict since 3E 427; **no Hist in the city**. → state §4, hist-placement |
| G2.8 | **Blackrose** | `FILLED` — whoever holds the island core; three-river transit and tolls; ruined-and-rebuilt quarters of several ages; a **drowned Hist** in the lake. → state §4 |
| G2.9 | **Alten Corimont** | `FILLED` — captain of the port; principled neutrality with a price list; the beached ship still the social hall; **no Hist**. → state §4 |
| G2.10 | **Every settlement's Hist** | `FILLED` — placement rule (R1–R6) plus a per-settlement register. → [../topics/hist-placement.md](../topics/hist-placement.md) |
| G2.11 | **Settlement magnitude** | `FILLED` — a six-class ladder defined in **structures, not people**, since canon gives no census and Phase 11 needs buildable scale. → settlement-register §1 |
| G2.12 | **Currency and exchange** | `FILLED` — three tiers: **septims still circulate** in the cities and ports (no mint replaced them), barter and obligation in the villages, nothing in the deep interior. → settlement-register §7 |

## 3. Secondary settlements

| ID | Question | Status |
|---|---|---|
| G3.1 | Which secondary settlements exist in 4E 201? | `FILLED` — every canon-named settlement given a 4E 201 status and class, plus proposed roles for the fifteen Arena-name settlements. → settlement-register §3–4 |
| G3.2 | The Argonian village baseline | `FILLED` — Hist, uxith, the canon office set, region-specific building materials, built to be replaced. → state §3, material-culture |
| G3.3 | Drifting / floating villages | `FILLED` (lore) + `DEFER` (implementation, **Phase 11/14**) — three distinct phenomena; only one needs engineering, and the recommendation is **exactly one** hand-authored drifting village with two or three seasonal moorings. → settlement-register §5 |
| G3.4 | Imperial-era toll-towns | `FILLED` — toll-taking is the normal form of rural revenue; **every bridge, ford, mangrove channel and portage has an owner**. → state §3 |
| G3.5 | Does Blackrose Prison operate? | `DECIDED` Q3 — **ruin reoccupied by the Blackguards' heirs**, Umbriel's undead below. → prisons.md, settlement-register §3 |
| G3.6 | Where is **White Rose Prison**? | `FILLED` — inland in the western burn country between Soulrest and the interior; abandoned, structurally sound, **full of Argonian dead who never got home**. → settlement-register §6 |
| G3.7 | Is **Fort Swampmoth** standing, and who holds it? | `FILLED` — on the Blackwood frontier commanding the road between Slough Point and Gideon; **held, but not by the Empire**. → settlement-register §6 |
| G3.8 | Where does an outsider legally enter? | `FILLED` — three legal entries and one loophole. → state §5 |

## 4. Factions

| ID | Faction | Status |
|---|---|---|
| G4.1 | **An-Xileel** | `DECIDED` Q1. → an-xileel.md, state §1–2 |
| G4.2 | **Archeins** (canon explicitly flags this gap) | `FILLED` — the *name* is now an insult nobody claims; the *families* largely survive, stripped of Imperial titles, rebranded, performing the same functions for the state. → state §2 |
| G4.3 | **Shadowscales** | `FILLED` — a last generation. Archon closed 4E 187, the last known Shadowscale dies 4E 201, the Black-Tongues have had nowhere to send hatchlings for fourteen years, and the Dark Brotherhood wants the school back. → sithis-nisswo-shadowscales, guilds-and-orders §3 |
| G4.4 | **Clutch of Nisswo** | `FILLED` — alive, itinerant, partially filling the ku-vastei vacuum, and structurally unable to become a judiciary because it has no central governance by design. → state §2 |
| G4.5 | **The Wild Ones** | `FILLED` — **not an organisation**: a category the An-Xileel named and claimed, the opposite number to *Lukiul*. Now a slur in both directions. One `AGENT_INVENTED` extension (surviving vigil-communities) raised as **Round 2 Q6**. → guilds-and-orders §5 |
| G4.6 | **House Dres / Morrowind** | `FILLED` — a cold, settled frontier; Argonians hold Scathing Bay and patrol occasionally; the Dunmer consider it long over. → state §5 |
| G4.7 | **The Empire** | `FILLED` — absent for two centuries, no official presence; Imperial *people* everywhere; at most a trade factor at Archon with no diplomatic status. → state §5 |
| G4.8 | **Thalmor** | `FILLED` — no presence; interest real, deniable, at arm's length. → state §5 |
| G4.9 | **East Empire Company** | `FILLED` — gone; its wharves and bonded stores are not. → state §5 |
| G4.10 | **Mages Guild / Synod / College of Whispers** (L24–L26) | `FILLED` — **no magical institutions in the province at all**, anchored on the canon datum that the Synod had no presence "for roughly 400 miles". Both successors operate through intermediaries: the Synod hunting artefacts, the College hunting **Umbrielic remains**. Plus the free canon link that **Hierem**, who set Umbriel in motion, was the Synod's most influential patron. → guilds-and-orders §2 |
| G4.11 | **Thieves Guild / Dark Brotherhood** | `FILLED` — no Imperial Thieves Guild; the native equivalents are Pusbottom, Alten Corimont, the Blackguards and the tribeless Naga. The Brotherhood's only route in was the Shadowscale pipeline and it is closed; its live interest is reopening Archon. → guilds-and-orders §3 |
| G4.12 | **Cyrodilic Collections** | `FILLED` — **revived**, and recommended sited at **Gideon**; its unbuilt museum is a genuine argument against a religion of letting go. → guilds-and-orders §4 |
| G4.13 | **Sul-Xan, Blackguards, Lut-Eileel, Four Winds, Veeskhleel, Xit-Xaht** | `FILLED` — all persist; each given territory and character as an attributable encounter-holder. → ecology-encounters-loot §3 |
| G4.14 | **Pirates** | `FILLED` — two grounds, two characters: Archon's ex-privateers with paperwork, and Bramman's heirs in the mangrove river. → state §5 |
| G4.15 | **The Conclaves and the cult of Seth** (new) | `FILLED` — orphaned colonial urban cults, mostly decayed; the **Conclave of Baal at Stormhold survives** because only it can locate Murkwood. The **Seth** cult is the best unclaimed religious hook in the corpus. → guilds-and-orders §2 |

## 5. Regional and economic

| ID | Question | Status |
|---|---|---|
| G5.1 | What does Argonia trade, and with whom? | `FILLED` — subsistence baseline, low-volume high-value craft exports, and an illegal trade whose flagship commodity is **Hist sap**. → state §6 |
| G5.2 | Who moves goods inland, and how? | `FILLED` — rafts and rootworms, which beat every Imperial road 5:1 on time and absolutely on spoilage. → state §6 |
| G5.3 | Are the eight cities connected by road, per the acceptance rule? | `FILLED` — yes, and **most of it is water**: a route with a maintained crossing at every water, closing seasonally. Trunk structure listed. → state §6 |
| G5.4 | Danger baseline, and does it differ for Argonians? | `FILLED` — **species-stratified**: the interior is lethal to outsiders as terrain. Canon's own principle, from the siting of Blackrose Prison. → state §7, ecology §1 |
| G5.5 | Flood/season cycle and how it gates movement | `FILLED` — wet / dry / wintertide, with route availability, water level and the rootworm line keyed to it. → ecology §6 |
| G5.6 | Are the quest plan's demographic priors defensible? | `FILLED` — broadly yes, with two corrections: Gideon is **canonically majority Lukiul**, and Thornmarsh is **grassland**. → state §4, quest-plan-deltas D7 |
| G5.7 | How many Hist, and where? | `FILLED` — density gradient R1, four kinds of tree R2, eight states R3, absence rules R4, continuous root layer R5, one-tree-one-look R6. → hist-placement |
| G5.8 | State of the pre-Duskfall ruin network | `FILLED` — four-state model (tended / inhabited / sealed / broken) with shares, and the rule that **a xanmeer's state is a social fact before it is a level-design fact**. → settlement-register §5 |

## 6. Deferred — technical, not lore

| ID | Item | Phase | Reason |
|---|---|---|---|
| D-1 | How a drifting village is represented at runtime | 11 / 14 | The lore answer is settled (one village, two or three seasonal moorings). What remains is a streaming and authoring choice. |
| D-2 | Exact xanmeer count and per-site interior graphs | 12 | The state model and shares are set; individual dungeon layouts are Phase 12 work. |
| D-3 | Encounter tables as data | 13 | Composition, territory-holders and loot provenance are specified; turning them into tables needs the Phase 13 schema. |
| D-4 | Hist as a placed entity with IDs | 11 | The register names every tree and its state; stable semantic IDs come with the Phase 11 location records. |
| D-5 | Seasonal state machine | 8 / 13 | The wet/dry/wintertide model is specified; water level and route gating are systems work. |

## 7. Mysteries — deliberately not to be closed

Canon leaves these open on purpose. Recorded so no future agent "fixes" them.

| ID | Mystery |
|---|---|
| G6.1 | **What Duskfall was.** Sources describe it only poetically. |
| G6.2 | **What the Eye of Argonia is.** Canon deliberately leaves its nature open; our functional reading is project layer and stays flagged as such. |
| G6.3 | **Whether there was ever a King of Black Marsh.** The Scalded Throne's existence is itself disputed in canon. |
| G6.4 | **Who made the Knahaten Flu.** Three incompatible accounts, all canon. |
| G6.5 | **Why the Argonians stopped fighting in 1E 2836.** No source knows. |
| G6.6 | **What the Hist actually are and want.** Every account is from outside or from a believer. |
| G6.7 | **What the "Wild Ones" meant to the people so named.** We have fixed what the *An-Xileel* meant by it; what the interior tribes thought of the label is a question the setting should keep asking. |

## 8. Quest assumptions

Claims a quest record needs that the lore does not state, added by `quest-write` §4b and checked by
`quest-review` item 17. Each row: id `QA<n>` (not the owner decisions Q1–Q5), the claim, status `ASSUMED`, the quest id, and the anchor it is the
least inventive reading of (file and section). A row may not contradict the lore or put a motif where
`story/design/province-vibe.md` §9 does not.

| ID | Claim | Status | Quest | Anchor |
|---|---|---|---|---|
| QA1 | The gang families of the Owing camp at the edge of Hereguard Plantation's paddies were sold on from the lower channel below Nine Bends to a Lilmoth broker, and so as not to wash out far from their tree they carried down a cutting of Nine Bends' Hist and planted it on the camp's own islet or bank, off the plantation's land, with the clutch laid at its roots; the cutting stays joined to its parent through the root network. When the cell's harvest cuts the cutting from the clutch, the cutting and its parent at Nine Bends withdraw together. | ASSUMED | quest.main.mq01 | `topics/labour-and-bondage.md` §2 (drift 2: an Owing sold on, worked far from home); `topics/hist-placement.md` Gideon row (a planted cutting; canon permits transplanting), Nine Bends row (the tree the gang families of the lower channel answer to, withdrawing over the dead clutch) and R5 (the root network); Hereguard's own row (no Hist of its own) still holds |
| QA3 | An ex-Archein family keeps an estate on the swamp road just north of Blackrose, worked by Owing debtors, with its own landing; a crossing-keeper holds the road's crossing beside it, apart from the estate. | ASSUMED | quest.bc.bc01 | `topics/labour-and-bondage.md` §2 (ex-Archein estates and their Owing debtors) and §3 (a toll-keeper owns a bridge, not an office); `blackrose.md` |
| QA4 | The heirs of the Rose keep an outer post at Blackrose's edge, where BM&V's own 'Black Rose Jail' marker stands, with cells under it; the prison proper still lies a day's march south, and town and Rose still share no government. | ASSUMED | quest.bc.bc02 | `topics/prisons.md` (the Rose a day's march from the city, no shared government; the heirs' own hierarchy); `blackrose.md`; BM&V's census (no land south of the town, so the prison itself is not visited yet) |
| QA5 | A young Argonian may walk out into the land beyond the settlement alone to prove themselves to the tribe, and the tribe's custom forbids its own to follow; the custom binds the tribe, not an outsider; the walk-out ends when they return. | ASSUMED | quest.local.lq30 | `extrapolation/argonia-4e201-state.md` §2 (Helstrom's guard a tribal levy, answerable to the interior assembly) and the tribes' rites of passage in `tribes.md`; the design LQ30 (50-side-quests) |
| QA6 | BM&V's unnamed Village east of Lilmoth, on the leech water, is Low-Reed Village: a small tribal village (its tribe left unnamed) of stilt houses at the reeds' edge, with a Hist of its own tended in a pool, an egg-tender, a tree-minder, a root-herald who speaks for it and whom both sides may choose to hear a dispute before the Hist, and a kaal (war-captain). It is not the Bright-Throats' village, which the lore puts on cliffs over Oliis Bay, and it is not the Hatching Pools. | ASSUMED | quest.main.mq04 | `regions/murkmire.md` (many small tribal villages with strong individual identity; disputes to an arbitrator both sides choose), `topics/hist-placement.md` (Tribal Hist), `topics/material-culture.md` (root-herald, tree-minder, egg-tender, kaal) |
| QA7 | A Lilmoth debt-labour broker holds the months of an Owing gang bought from earlier holders, adds months for its food, and hires it out to Hereguard Plantation; his overseer reads the roll aloud at his barge at Dock1, and a broker is a local trader, not an office of the state; he will sell an Owing's months back to the debtor's side for coin. | ASSUMED | quest.main.mq01 | `topics/labour-and-bondage.md` §2 (drift 2: an Owing sold on; drift 3: an Owing extended by the debtor's food) and §3 (port docks run indentured crews); `extrapolation/quest-plan-deltas.md` Q7 (a local arrangement, not the state's) |
| QA8 | The Veiled Reed's protection of a person in Lilmoth is given deniably through a local intermediary, a fish-trader who keeps an unmarked house for it and also sells to the trade it touches (here the debt-labour broker): the Reed's own people wear no mark and never show the broker a face; its backing is coin and knowledge passed through the intermediary's hands, and nothing is written. | ASSUMED | quest.main.mq03 | `design/quests/10-political-frame.md` §6 (the Reed works deniably); `design/province-vibe.md` §8-9 (state institutions work through intermediaries; Lilmoth denies the state); `lilmoth.md` |
| QA9 | The Veiled Reed may send an unmarked hand after a matter on tribal ground, who keeps off the village's land in a boat on the open water and speaks ashore only through a Lilmoth go-between; he takes away people the village has handed him and leaves the village's Hist and its sap to the village: no one, Reed or state, claims a tribal Hist. | ASSUMED | quest.main.mq04 | `design/quests/10-political-frame.md` §6 (the Reed works deniably); `design/province-vibe.md` §8-9 (institutions work through intermediaries; no state officials on tribal ground); `extrapolation/argonia-4e201-state.md` §1 (almost no writ inland); QA8 (the Reed's intermediary in Lilmoth) |
| QA10 | In Helstrom a hall holds the state's formal seat, the Scalded Throne, a plain root-and-reed seat that has stood empty for centuries, is swept daily by a hall hand, and is largely ignored by the city, which sells in the room before it. | ASSUMED | quest.main.mq05 | `extrapolation/argonia-4e201-state.md` §2.2 and the Scalded Throne paragraph; gap-register G6.3 (whether there was ever a King of Black Marsh); `topics/sithis-nisswo-shadowscales.md` |
| QA11 | The sap of a Hist cut at the root, spilled, draws the leeches of the water about it, and the sap returned to the root with the cut washed lets a severed Hist's next clutch be laid. | ASSUMED | quest.main.mq04 | `topics/hist-and-sap.md` (sap is the Hist's soul; Silence vs severance: unborn eggs die of the severance); BM&V's Village leeches (adaptation.md §5 MQ04) |
| QA12 | Helstrom has a house where travelling Nisswo lodge and hold their debates before the city, a plain house with no resident order and no central body. | ASSUMED | quest.main.mq05 | `topics/sithis-nisswo-shadowscales.md` (the Nisswo travel and have no central doctrine); `helstrom.md` (a city-state with its own houses and alleys); BM&V's Helstrom npc rows (a Nisswo interpreter at a debating house) |
| QA15 | A tribal village whose Hist's matter a stranger has put right takes that stranger in as kin for as long as they keep faith with it: its root-herald gives a bed and food at the village's cost and its tree-minder's sap-balm heals, with no price (the village trades in reciprocity); a village that gave a man it held to a stranger's boat keeps cool with the player who gave him. | ASSUMED | quest.main.mq04 | `regions/murkmire.md` (many small tribal villages with strong individual identity); `design/province-vibe.md` §5 (villages trade by reciprocity, not price); `design/quests/30-main-quest.md` §24b.3 tier 1 (adoption by a village); QA6 |
| QA18 | The first sap-dream (a ring of trees, a door nobody built, a dry voice) reaches a player who is not an Argonian as the hallucination Hist sap gives them, with the same ring, door and voice in it; the bloodlust edge of that hallucination is a dry anger that has passed by waking, one small taste being far below an overdose; on an Argonian, whose cut Hist it is, the sap does the same ('Sap': mistreat the tree and the sap does the same to Argonians). | ASSUMED | quest.main.mq03 | `topics/hist-and-sap.md` 'Sap' (licking sap brings visions; on non-Argonians a hallucinogen that induces bloodlust); `design/quests/30-main-quest.md` §18d (the dreams, the unplaced voice) |
| QA19 | The grove behind Helstrom's hall rises into a crown that is reached by root-ladders of flint vine, where a tree-minder of the assembly keeps a watch over it; a stranger may climb to her. | ASSUMED | quest.main.mq05 | `topics/material-culture.md` (flint vine is canon cordage 'strong enough to haul heavy objects or be made into a rope-ladder'; root-training); `topics/hist-placement.md` (Helstrom: a grove, not a tree); `extrapolation/argonia-4e201-state.md` §2.2 (an assembly of naheesh and tree-minders); Lilmoth's tree-minder's post is a vigil (hist-placement) |

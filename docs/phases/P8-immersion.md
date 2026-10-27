# P8: Immersion to 100%: no Nordic element, new music, final look

**Goal.** Every element in the immersion inventory has a verdict and a passing check, across the whole load
order (not just the slice): every UI surface restyled, every reachable asset Black Marsh-appropriate, new music
for every music type, the vanilla quarantine complete, and the final graphics look (light, fog, volumetrics,
water) tuned. After P8, everything new in P9 enters the inventory already compliant.

**Starting state.** P7 passed; the inventory exists (P2) and the slice's rows are closed.

**Read first.** Decisions 0006 (in full, including §7 AI clause and §8 Tropical Skyrim) and 0012;
[assets-creatures](../research/2026-10-27/assets-creatures.md) §3d; [legal-and-sourcing.md](../legal-and-sourcing.md).

## Work packages

### WP8.1 Inventory completeness
- Re-run the inventory over the full load order and the whole world plan (all regions, including not-yet-built
  places' planned contents from the catalogue). Reachability now includes everything any P9 packet can place.
- Group rows into **work queues** by kind (UI, item meshes/textures, creatures, NPC appearance, flora,
  architecture, sounds, music, text, loading screens, menus, effects).
- **Acceptance:** counts per queue and per verdict published in PROGRESS; zero rows without a queue.

### WP8.2 Verdicts at scale (the agentic coverage method)
- For each queue: a cheap first pass decides `keep` / `restyle` / `replace` / `hide` / `remove` from data
  (names, keywords, source mod, Nordic-term list) and a contact-sheet capture (L4 batch renders of the
  element: icon, mesh in a lit booth, texture swatch) judged by `reader` agents with the Nordic-tells checklist;
  uncertain rows go to a second reader; disagreements and samples (5% of each queue, minimum 10) go to the owner
  as a packet.
- Replacement order: Black Marsh mods → Tropical Skyrim (SSE 78044) → other permitted mods → a retexture or
  recolour of the existing asset (a "minor tweak", allowed) → a Fal-made 2D element (UI, icons, paintings,
  map, decals) → `hide`/`remove`. No new meshes.
- Every replacement is a record override or a file reference in our plugin; no third-party files are copied
  into our archives.
- **Acceptance:** zero reachable rows without a passing check; the owner's sample packets agree with ≥ 95% of
  sampled verdicts (disagreements fixed and the rule that caused them updated).

### WP8.3 UI, menus, fonts, loading screens, main menu
- Re-run the P4 UI map's transition loop over the whole game (every screen and transition now reachable,
  including those P5–P7 added: boss bars, boat wind call, climbing stamina, death/wake), same method: L5 clips
  judged by readers, then an owner packet.
- Our own views (decision 0017) cover every major screen and the HUD from P4. Here: every remaining vanilla menu in the stack (including MCM, tween menu, system menu, journal tabs we kept, crafting,
  lockpicking if kept, training, sleep/wait, loading menu, main menu, credits) restyled or replaced by the decision
  0014 §7 order (PrismaUI replacement, our own original SWF, installer-time patch; never a shipped edit of a
  Bethesda or mod SWF); Pelagiad
  verified everywhere; icons replaced (Fal for any icon with no sourced equivalent).
- Loading screens: Black Marsh paintings (Fal-made or sourced) with loading facts from the text catalogue
  (old "the marsh does what the loading facts say", 0157).
- Main menu: Argonia title, Black Marsh background scene, Pelagiad.
- **Acceptance:** a full menu sweep (every screen, every tab, 1080p and 720p) passes the reader panel and an
  owner packet.

### WP8.4 Music and sound (owner call O-8)
- Music types: exploration by region and time of day, combat (normal, boss), dungeon, town, menu, death,
  discovery, level sitting, rest. Sources in decision 0006 §5 order: CC0/CC-BY music (credited) → commissioned
  → Fal-generated (if no dependency's AI clause forbids it). MUSC/MUST records replace every vanilla music type;
  a bridge check confirms no vanilla track can play.
- Ambience and UI sounds: Black Marsh soundscape (insects, frogs, rain on leaves, water) from permitted sources;
  Nordic-flavoured UI sounds replaced; creature sounds checked.
- Voice: barks and combat shouts filtered to an allow-list (decision 0012 §4).
- **Acceptance:** a 30-minute L4 audio log (music types and sound descriptors played) shows no vanilla music and
  only allow-listed voice lines; an owner listening packet.

### WP8.5 Vanilla quarantine complete (decision 0012)
- Extend the P2 scenario to every vanilla system: dragons, shouts, word walls, Dragonborn wording, Sovngarde,
  civil war, standing stones, couriers (Dark Brotherhood letter, inheritance), radiant quests, guard chatter,
  Helgen, the Tamriel worldspace, Skyrim's world map, constellation perk menu, Skyrim races' Nordic text.
- **Acceptance:** the 50-day scenario passes; text search of every reachable string finds none of the Nordic
  term list.

### WP8.6 Final look: light, fog, volumetrics, water, weather
- Community Shaders presets per region and weather: humid marsh light, volumetric fog and god rays through
  canopy, marsh mist, waterfall mist, rain; water shader tuned for murky fresh water vs sea; image spaces; all
  measured against the G2 frame-time bar on the chosen instance.
- Use RenderDoc captures on the GPU box (Linux/Proton supports it) for pass order and fog parameters when a look
  question cannot be answered from settings.
- Reference: the old project's look decisions (haze by default, old 0136; light and world time, old 0016; mist
  volumes, old 0124) and its screenshots.
- **Acceptance:** reader panel on a 50-shot vantage set across regions and weathers; owner look packet; frame
  time within the bar.

## Exit gate
Inventory 100% (no reachable row without a passing check); music and sound complete; quarantine scenario green;
final look approved by the owner; the gate now enforces compliance for every new element.

## Risks and fallbacks
- **Volume**: the inventory may run to tens of thousands of rows; data-first verdicts and batch contact sheets
  keep reader cost proportional; the owner sees samples, not everything.
- **AI clauses** limit Fal use where a dependency forbids AI: such rows fall back to sourced or CC art, or the
  dependency is reconsidered.

## Deliberately out of scope
New meshes (never); content building (P9); voice acting (unvoiced, O-11).

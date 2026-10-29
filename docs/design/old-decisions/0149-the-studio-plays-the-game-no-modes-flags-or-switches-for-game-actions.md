<!-- imported unchanged from elder-souls-argonia docs/decisions/0149-the-studio-plays-the-game-no-modes-flags-or-switches-for-game-actions.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0149 The studio plays the game: no modes, flags or switches for game actions

**Decision (owner, 2.9x close).** The owner's words, verbatim: "get rid of
all the dumb 'fight mode' stuff and options from the studio and the dev
panel; this is just a coherent game that we're making (mostly morrowind and
skyrim shaped with dark souls combat, was broadly our overall goal) and the
studio is where we're testing our systems out, not something where you have
some weird url flag or whatever just to draw your sword and do combat!
Preserve this steer from me where appropriate so no other agents will make
similar mistakes in future (for combat or any other game system)."

1. **The studio runs the game's own systems the way the player reaches
   them.** Drawing a weapon, equipping, casting, resting, trading, sailing:
   every game action is reached in the studio exactly as in the game (the
   inventory, the belt, the buttons, the people). No URL flag, studio mode,
   preset picker or dev-panel switch stands in for a game action, for combat
   or any other system.
2. **What debug UI may do.** Observe (overlays, counters, the free camera)
   and move the tester about (teleport, time of day, weather). A control that
   changes what the player can do is a game feature and ships in the game, or
   it does not exist.
3. **Capture tooling is not studio UI.** A pod capture may grant a kit or
   trigger an action through its own hook so a scene can be shot in seconds;
   that hook lives in the capture tooling, never as a studio option, and a
   journey loop reaches the same state through the player's own flow at least
   once.
4. **Why.** Modes split the tested thing from the shipped thing: the 2.9x
   deployed build had a roll that did nothing and a touch layer with no
   combat buttons because the studio's fight mode had been tested instead of
   the game's draw-and-fight flow.

Applies through CLAUDE.md § Code; the `fight=` token and `studioFight.tsx`
preset picker are deleted by the 2.9x journey lane.

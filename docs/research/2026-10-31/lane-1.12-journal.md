# Lane 1.12-journal: the journal and the dialogue window (1.12 §6)

## What changed
- **Schema** (`ui/schema/journal.ts`, `dialogue.ts`; twins regenerated): `journal.state` v2 and `journal.page` v2
  (ribbons `current | finished | all | topics`, `groups` by questline or place, the opened `quest` with its latest
  `directions` and entries newest first, `search`, `matches`); `dialogue.state` v2 gains `services` (`barter`), and a
  new intent `dialogue.service` v1.
- **Grouping from the records**: `tools/argonia_world/quest_gen.py` emits `kJournalQuests` into `journal_text.h`
  (quest title, questline name and group, place = settlement else first anchor place) from the world database via
  db.py. Rule in `skse/core` (`journal::group_of`): a `local` questline's quest is listed under its place (LF83 under
  "Claywater Station"); any other under its questline.
- **Rules in skse/core** (`views::journal_state`, `journal::matches`): Current = active, Finished = complete and failed;
  groups ordered by their most recently written quest; the quest asked for, else the most recent listed, opens on its
  latest direction (active only), then entries newest first; All entries = the diary oldest first, paged; search =
  every word, ASCII case-insensitive, over quest name and entry text; Topics empty (2.12).
- **ArgoniaCore**: `views.cpp` journal builder passes `entry_group`, opens on Current; `dialogue.cpp` adds Barter
  when the speaker has a vendor faction: our view hides (conversation kept), `RE::BarterMenu::OpenMenu` next frame
  (Wind UI draws it), and on BarterMenu close the same conversation is pushed back.
- **Views**: the journal is the paper book inside a frame-style window (bar with title, search field and Close;
  bookmark ribbons; two leaves). The dialogue window moved from parchment to the frame tokens and shows Barter.
- **Harness**: journal stills/wiring updated (ribbons, search by "/" + typing, open quest, touch B close, Barter); the
  off-screen measure now judges each visible line box (text in CSS columns spans leaves the scroller hides).

## Design calls (the agent's latitude)
- Search: a real text field ("/" or Ctrl+F reach it; typed keys stay in it; Esc in it clears); B always closes.
- On Current/Finished the pad's shoulders step the ribbons; on the diary they turn pages.
- Mock quests in the fixture (`quest.mock.*`) are labelled mock; LF83's words are the records'.

## Not done / risks
- ArgoniaCore was not compiled here (no CommonLib on this VM); `dialogue.cpp` uses `GetVendorFaction`,
  `RE::BarterMenu::OpenMenu` and `MENU_NAME` as engine.cpp already does. First deploy build proves it.
- The topic action `openBarter` (engine.cpp, lane trader) still closes the conversation; only the Barter button returns.
- Touch B in the journey is the pad's B (assumes the phone's touch overlay sends the pad's B).

## Evidence
- `bash skse/check.sh`: 33/33 ctest passed (new: the_journal_ribbons, grouping/search in test_journal).
- `make ui`: green. L3: `python -m tools.ui_harness` 168 stills, 0 fails, wiring green; stills under
  `out/ui/stills/{journal,dialogue}/` at 1080p, 720p, v5-folded, v5-unfolded.
- Journey: `tests/journeys/journal-dialogue.yaml` (engine-route keys; for the coordinator's batch, last in batch).

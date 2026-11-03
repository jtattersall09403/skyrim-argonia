# Lane 1.12-r5-settings-page (2026-11-03)

## Path
Our System pane -> `system.pick settings` -> menus.cpp presses the Journal Menu's System page entry; `FrameMovie` hides
the tab bar and logs `menus: Journal Menu handed over (tabs hidden: ...; ... has ...)`. The art is Dear Diary's
quest_journal.swf + deardiary/quest_journal/quest_journal_BG.swf (wood-and-paper wins), recoloured at install by
tools/ui_theme/retheme.py FRAME (FramePalette).

## Findings
- Journey expectation fixed: "Journal Menu restyle (tabs hidden: QuestsTab" -> "Journal Menu handed over (tabs hidden: QuestsTab"
  (menus.cpp:130; the old text was replaced when the run-time tint was removed, part 3).
- The theme as built here (stack argonia-theme, 11:27) is already in the frame style: reader on the BG bitmap: near-black
  green ground, gold-green trim, no torn edges, no rivets; text fields (230,220,178) on ~(13,21,15) is far above 4.5:1.
  The source BG (wood-and-paper) is beige with tabs only mildly ragged, and has no rivets either.
- So the batch still (rivets, torn edges, dark list text) is not this art: either the game machine ran a stack whose
  argonia-theme did not place quest_journal (stale deploy, or the "custom UI" card that sets aside dear-diary/theme
  paths), or another layer draws the frame. Not decidable without the batch deploy record or a still; stills are not on disk here.
- Residual risk: list entry colours are set at run time by QuestCenteredList.SetEntryText (textColor, bytecode
  constants) in quest_journal.swf; retheme.recolour_text only maps DefineEditText colours, so list rows may still be
  dark. Needs a bytecode constant patch (not done; scope change).

## Owed
checks.md row for the planner's menus-look run: 09-system-settings reads as our frame (dark ground, trim, light legible
labels, nothing clipped), after confirming the game machine's stack holds the current argonia-theme (UI variant windui).

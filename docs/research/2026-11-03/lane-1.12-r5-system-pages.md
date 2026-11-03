# Lane 1.12-r5-system-pages: the Journal's System page (Settings, Load) in the frame style

Status: evidence named (step 1); retheme in progress.

## The frame art

- The "cream ragged frame" is not another asset: it is Wood and Paper's `interface/deardiary/quest_journal/quest_journal_BG.swf`
  bitmap #14 (1036x687, DefineBitsLossless2), already in the overlay (`argonia-theme.json`: "recoloured #14 1036x687").
  FramePalette maps its ragged wood band (saturation >= 0.45, luminance < 0.28) onto `frame-trim`..`frame-trim-hi`
  (#8a8a4a..#b5a862), so the torn edge reads as a wide cream-yellow band; the recolour keeps the shape.
- The header slot bars, the bottom "Level" well and the Cancel tab are parts of the same bitmap (its top strip, bottom
  strip and lower-left tab), not separate art.
- `interface/quest_journal.swf` (Dear Diary) embeds 118 32x32/32x64 tiles (#1-#118, grey) and #350 (12x178), #355
  (687x1036, fully transparent); none is the frame. No DDS is drawn by these pages; imports are gfxfontlib,
  skyui/buttonArtDD.swf and skyui/ConfigPanel.swf (ConfigPanelFader) only.

## The run-time text colours (quest_journal.swf, Dear Diary 3.0.5; tag index in swf.read order, offset in tag data)

| tag | class | offset | value | use |
|---|---|---|---|---|
| 533 (DoInitAction) | Shared.BSScrollingList (SetEntryText) | +7675 | 0x000000 | row text, `enabled` branch (category list, left list, save list) |
| 533 | " | +7688 | 0x640000 | row text, other branch |
| 533 | " | +7746 | 0x000000 | row text, `disabled` branch |
| 533 | " | +7759 | 0x640000 | row text, other branch |
| 542 (DoInitAction) | QuestCenteredList.SetEntryText | +389 | 0x000000 | row text, `completed` branch |
| 542 | " | +402 | 0x053405 | row text, other branch |

Each is an ActionPush int32 feeding `textField.textColor` (SetMember); recolour_text only reaches DefineEditText
colours, so these stay black on the new dark ground.

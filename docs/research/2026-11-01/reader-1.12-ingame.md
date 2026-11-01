# Reader 1.12 in-game stills (images mode)

Reference: /home/ubuntu/skyrim-argonia/tmp/image.png. A, P, J, S are the batch folders from the brief.

## Per still
- A/03-minimap-north: PASS. Round parchment minimap top right, gold-green rim, red arrow at centre pointing up, N plate at top, no Skyrim compass bar, "Menu" button below it. No effects stack visible (none active), so its clearance of the bottom corners is not shown.
- A/04-minimap-135: PASS. Rose turned so N sits lower left, arrow still up. A small black triangle sits at the right screen edge (x~1910, y~663), source unknown.
- A/06-chart-open: FAIL. Parchment chart in a dark green-black frame with gold-green trim, red arrow at the player's place on the west edge (550,432). No warmer revealed land along a walked road is visible. No quest markers, but 8 named places are labelled (Stormhold, Thorn, Gideon, Archon, Soulrest, Blackrose, Lilmoth).
- A/07-chart-zoomed-out: PASS. Dashed northern edge (y~42) through the southern coast (y~920) inside the sheet, arrow shown. It is pixel-for-pixel the same view as 06, so a zoom-out is not demonstrated. West rivers run off the province strip at x~505.
- A/02 + A/12: FAIL. 02 is the plain HUD with no chart. 12 labels Claywater Station by name with the arrow near it (539,419), but the other seven places are labelled too, same as 06. The Claywater label has no small place mark or plate, unlike the others.
- P/01-start-opens-windows: PASS. Character, Inventory, Magic and the taskbar are open, near-black panes with thin gold trim, no knotwork, no HUD over them. Stray faded text "MCM Registered 1 new menu" bleeds over the top-left of the CHARACTER title. Steel Sword slot shows tiny text, no icon.
- P/07-bumper-to-journal: PASS. Journal in a dark green frame with paper pages, empty "No quest is under way." The frame is translucent: Character and Magic text and the taskbar ghost through its header and bottom edge.
- P/09-bumper-to-map: FAIL. Only Wind UI Character, Inventory and Magic windows are shown. No chart.
- P/11-bumper-to-system: FAIL. Same three Wind UI windows, with a ghost parchment frame behind them (faint "No Active Quest" text, an empty bar at 1087,865). No System page, so sentence case and squash are not testable.
- P/20-keyboard-system: FAIL. Same as 11, no System page.
- P/14-select-waits: PASS. Parchment panel in a green frame, "Wait how long?", slider at 1, "Sundas, 10:09 AM, 15th of First Seed", A Yes / B No. The date format differs from the journal's "15th of the Third Month, 201".
- J/02-dialogue-topics: FAIL. Dark pane, gold-green trim, warm serif, four topics plus Goodbye, Disposition 25. The greeting has no highlighted keyword links, and "Claywater Station" shows only as a heading above the reply.
- J/04-hud-notice: PASS. Dark strip "Journal updated" with a blue left accent under the Vastei counter. "E Talk Takes-The-Short-Weight" prompt below.
- J/05-journal-current: PASS. Claywater Station group, quest "The Well and the Landing", right page opens on "Where next". Dated entries are not in view; the text is cut mid-line at the bottom behind a scrollbar.
- J/08-barter: PASS. Wind UI Inventory plus "LIVIA VARINIUS" vendor pane, Offer/Cancel, "Nothing on offer". Black polygon artefact in the world top left (x140-620, y400-470).
- J/09-barter-returns: PASS. Dialogue frame back with Livia Varinius, "The well" highlighted and underlined, Barter and Goodbye buttons, Disposition 45.
- J/12-journal-finished: PASS. Finished tab active, quest struck through with red "Failed", entry "15th of the Third Month, 201". Text cut mid-line at the bottom, scrollbar present.
- S/03-rest-opens-sitting: PASS. Dark green-black pane, gold-green trim, "Level 2", attribute rows with Buy, "Rise", "Health 44 -> 48". Agility and Speed dimmed "Not enough vastei".
- S/05-stats-pane: PASS. "Perk points 1", Block Perks list (Bulwark 0/5, Deflect Arrows, Elemental Protection, Block Runner, Power Bash, Deadly Bash, Disarming Bash, Shield Charge, Quick Reflexes). No Nordic word and no level-up window. Header still says "Level 1" after the sitting said Level 2. The hover tooltip hides "Heavy Armor".
- S/06-perk-taken: PASS. "Perk points 0", "Points 0", Bulwark (1/5), tooltip "Your blocks are 25% more effective." The tooltip covers the Histskin row and the perk level numbers.

## Open judgement
1. One design: the dialogue, sitting, journal frame and HUD share dark green-black, gold-green trim and a warm serif. Wind UI panes are flatter and near-pure black with thin hairline trim and an all-caps title font, so they read as a sibling, not the same family as the reference's textured green-black panes with carved corners.
2. Nordic and Skyrim: no knotwork or Nordic ornament seen. Skyrim leftovers: "Voice -" slot in the Magic pane, "Steel Sword" and vanilla perk names (Bulwark, Deflect Arrows...), "Blackwood Road" is fine. Perk names need the 0012 review.
3. Squashed or cut off: the chart is a narrow centre strip with blank parchment either side and the west edge clipped. Item slot labels are tiny two-line text. The Character skill list is cut mid-row ("Illusion"). Journal body text is cut at the page foot.
4. Overlap: the journal frame is translucent over Wind UI windows (07), a ghost parchment sits behind the windows (11, 20), and the MCM debug text sits on the CHARACTER title (01).
5. Worst first: chart, System page and pad map stills (09, 11, 20) do not show the screens they claim. Then the chart's missing revealed land and the other places labelled in 12. Then dialogue keyword links in 02. Then the ghosting. Date formats and Level 1 vs 2 disagree.

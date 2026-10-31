# Lane 1.12-design: Wind UI's frame retint (partial)

Commit 765110d. Status: (1) and (4) done; (2) and (3) not closed; (5) owned by the labels lane (tools/ui_theme/labels.py).

## Found
- Wind UI's log names the sources: panel9 and knot from the 63,896-byte vanilla `interface/inventory components/itemcard.swf`
  (from `Skyrim - Interface.bsa`; no mod in our stack lays it), the caps from our 23,994-byte `interface/tweenmenu.swf`.
  It finds each piece by size, so the recipe changes colours only.
- Drawing every shape's outline (scratch tool, stills private in argonia-private/work/windui-art/) shows Nordic interlace in
  itemcard #78 (the knot) and tweenmenu #48 #53 #55 #57. The itemcard frames (#32 #64 #111 #144 #202 #216 #219) carry small
  knotted corner squares inside the same shape: recoloured, not removed (needs geometry edits: open).

## Built
- `tools/ui_theme/windui.py`: every shape colour of both files on a luminance ramp (`--frame-ground` #0e130d, `--frame-trim`,
  `--frame-trim-hi`), the knot shapes cleared (alpha 0, else ground); called from `tools/ui_theme/build.py` after the retheme.
  Unit test `tools/ui_theme/tests/test_windui.py`; tools/ui_theme 15 passed.
- ui/DESIGN.md: frame tokens with reasons, Wind UI's art section, the UI map (every screen, who draws it).
- installer/steps/ui-theme.md step 2b. Stills batch: tools/ui_harness/windui_stills.sh.

## In game (argonia-play, job wu)
- Deploy built both files (itemcard 91 colours, knot #78 cleared; tweenmenu 45 colours, 4 knots cleared).
- WindUI.log: "menu art: 4 pieces ready in 87 ms (0 from the cache, 4 drawn, 0 not in the game's menus)": the retint is read.
- Stills did NOT show Wind UI's windows: TAB showed play, I showed Dear Diary's tween menu, Esc the System page. So no still of
  the retint yet; why Wind UI did not intercept after this deploy (key timing, or vanilla.txt / the stack push) is open.
- No reader verdict and no off-game render set (3) were made in this context.

## Next
1. Diagnose the intercept (WindUI.log after I; vanilla.txt on the machine), re-shoot 01-04, reader pass against tmp/image.png.
2. Corner knots of panel9: replace the corner sub-paths or pick a knot-free card shape of the same size.
3. The off-game set at 4 sizes through tools/ui_harness.

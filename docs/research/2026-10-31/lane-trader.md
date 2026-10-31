# Lane trader: hand-off

Done (c745ef3, `make check` green): Livia is Claywater's general trader. `npc_trade` holds her barter gold (300) and
hours (08:00-20:00); `trade_class_stock` holds trade-class.general's 17 items (Black Marsh items first, then reviewed
base items). `place_build._traders` generates the vendor FACT (Vendor, hours, not-sell/buy FLST, chest, near her ACHR),
the chest CONT in the door-less cell ARG_Cell_ClaywaterStationMerchantChests, and her NPC_ in that faction. The
`openBarter` verb runs her service topic `topic.service-barter` ("What do you have for sale?", text-reviewed). Service
topics are offered before the player learns them. ArgoniaCore closes our conversation and calls RE::BarterMenu::OpenMenu
on the next frame. Barter steps are in ui-review.yaml and ui-sweep.yaml.

Left:
1. The ArgoniaCore build (`trader-skse`, job_guard --gpu) is queued behind g18b on argonia-play. Read
   ~/.argonia/jobs/trader-skse.log. Fix any compile error in skse/ArgoniaCore/src/engine.cpp `open_barter`.
2. L4: run the barter-talk, barter and barter-closed steps (ui-sweep or ui-review) in the next game-machine batch.
   Unproved risks: whether OpenMenu needs the vendor faction calculated first (the log line prints its FormID), and
   whether radius 0 near her ACHR passes the vendor location check.

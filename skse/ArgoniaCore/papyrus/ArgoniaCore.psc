Scriptname ArgoniaCore Hidden
{ArgoniaCore's Papyrus natives (skse/ArgoniaCore). Logic stays in the plugin; scripts only call through. No condition
is evaluated here: the quest natives change state, and ArgoniaCore steps the watched quests itself.}

; The plugin's build version, e.g. "0.3.0".
String Function Version() global native
; Saves this playthrough has written with ArgoniaCore loaded (the META co-save family).
Int Function SaveCount() global native

; --- The quest natives (1.4's generated fragments; one per action verb, docs/research/journals/quests.md) ---
; Stage 0: ArgoniaCore steps this quest's stage graph on every fact change (SetObjectiveCompleted, SetStage).
Bool Function WatchQuest(Quest akQuest) global native
Bool Function UnwatchQuest(Quest akQuest) global native
; aiKind: 0 progress, 1 complete, 2 fail. Dated with the game calendar; once per stage.
Bool Function AddJournalEntry(Quest akQuest, Int aiStage, Int aiKind) global native
Bool Function GrantTopic(String asTopic) global native
Bool Function SetFlag(String asFlag, Bool abValue) global native
Bool Function ApplyLocalVariant(String asPlace, String asVariant) global native
Bool Function SetPrice(String asService, Int aiPrice) global native
Bool Function GiveItem(String asItem, Int aiCount) global native
Bool Function TakeItem(String asItem, Int aiCount) global native
Bool Function GiveGold(Int aiAmount) global native
Bool Function TakeGold(Int aiAmount) global native
Bool Function ChangeDisposition(String asNpc, Int aiDelta) global native
Bool Function ChangeSettlementStanding(String asSettlement, Int aiDelta) global native

; A quest thing's activate hook (ARG_PRKF_ThingHook, 1.4): the reference's base sets its flag (the thing table).
Bool Function ThingActivated(ObjectReference akRef) global native

; --- The dialogue intercept (ARG_PRKF_DialogueIntercept) and the view host ---
Bool Function OpenDialogue(ObjectReference akSpeaker) global native
; Any view's intent as the schema's JSON (ui/schema), routed by its type (dialogue.*, sitting.*, view.close);
; returns the view's next state, "" when it closed.
String Function ViewIntent(String asJson) global native
; The last state pushed to a view ("dialogue", "sitting", "journal", "hud", "chart"), "" when none.
String Function ViewState(String asView) global native

; --- The sheet's attributes (canonical in the STAT family; mirrored into reserved actor values) ---
Float Function GetAttribute(String asAttribute) global native
Float Function SetAttribute(String asAttribute, Float afValue) global native

; --- Reads for the L4 journeys ---
String[] Function Families() global native
String Function FamilyDigest(String asFourcc) global native
String[] Function RouterLog() global native
Bool Function GetFlag(String asFlag) global native
Bool Function KnowsTopic(String asTopic) global native
Int Function GetDisposition(String asNpc) global native
String[] Function JournalEntries() global native

; --- Grow, die, rest, save (1.5) ---
; Called by ARG_PRKF_RestIntercept: rest at the camp spot (false when refused; RestNotice() says why).
Bool Function RestAt(ObjectReference akSpot) global native
String Function RestNotice() global native
; Called by ARG_PRKF_RestIntercept: take the vastei pile back; the amount, or -1 when out of reach or gone.
Float Function TakeVastei(ObjectReference akPile) global native
; The sitting view's intent (sitting.buy, sitting.done) as JSON; the new sitting.state, "" once it closed.
String Function SittingIntent(String asJson) global native
; The hidden suspend save: "quit" or "stream_drop" (the bridge calls it by core-suspend); true when queued; any
; other word is refused.
Bool Function SuspendSave(String asWhy) global native
; Reads for the L4 journeys, and the scenes' step-0 setter of carried vastei.
Float Function GetVastei() global native
Float Function SetVastei(Float afValue) global native
Int Function GetPendingLevels() global native
Int Function GetLevel() global native
Float Function GetSkill(String asSkill) global native
; "x y z space vastei" in metres and the space's FormID in hex, "" when there is no pile; WakePoint likewise.
String Function PileState() global native
String Function WakePoint() global native
Bool Function SittingOpen() global native

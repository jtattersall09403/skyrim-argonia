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
Bool Function ChangeDisposition(String asNpc, Int aiDelta) global native
Bool Function ChangeSettlementStanding(String asSettlement, Int aiDelta) global native

; --- The dialogue intercept (ARG_PRKF_DialogueIntercept) and the view host ---
Bool Function OpenDialogue(ObjectReference akSpeaker) global native
; A view's intent as the schema's JSON (ui/schema); returns the view's next state, "" when it closed.
String Function ViewIntent(String asJson) global native
; The last state pushed to a view ("dialogue", "journal", "hud", "chart"), "" when none.
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

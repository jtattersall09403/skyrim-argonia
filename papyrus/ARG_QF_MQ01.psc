Scriptname ARG_QF_MQ01 extends Quest Hidden
{MQ01 No Name on the Work Roll (quest.main.mq01), the new game's opening, started by MQ101's override (ARG_QF_MQ101).
Character creation is the processing (as ARG_StartQuestScript did for Phase 1), then stage 10 in the barge hold. The
stage fragments and the helpers the lines call; shapes from Phase 3's blocks (docs/design/blocks.md).}

ObjectReference Property StartMarker Auto
Armor Property Tunic Auto
Armor Property Footwraps Auto
GlobalVariable Property RollRead Auto
GlobalVariable Property Answered Auto
GlobalVariable Property SavedSal Auto
GlobalVariable Property SavedDeesh Auto
ObjectReference Property CampOrderly Auto
ObjectReference Property CampAttacked Auto
ObjectReference Property CampAftermath Auto
ObjectReference Property MarchParent Auto
ObjectReference Property HoldParent Auto
ObjectReference Property CrewParent Auto
ObjectReference Property BrokerParent Auto
ObjectReference Property CellParent Auto
ObjectReference Property SurvivorsParent Auto
ObjectReference Property Shore93Parent Auto
ObjectReference Property ShedZone Auto
ObjectReference Property HutsZone Auto
ObjectReference Property ShedMark Auto
ObjectReference Property HutsMark Auto
ObjectReference Property ShoreMark Auto
ReferenceAlias Property Courier Auto
ReferenceAlias Property Leader Auto
ReferenceAlias Property SalSei Auto
ReferenceAlias Property DeeshDuun Auto
ReferenceAlias Property WuleenMarch Auto
ReferenceAlias Property UxMarch Auto
ReferenceAlias Property DivesMarch Auto
ReferenceAlias Property FindsMarch Auto
ReferenceAlias Property Ties Auto
ReferenceAlias Property Cutter1 Auto
ReferenceAlias Property Cutter2 Auto
Weapon Property ReedKnife Auto
Quest Property NextQuest Auto
ObjectReference Property FireMark Auto
ObjectReference Property HoldDoor Auto
ObjectReference[] Property Zones Auto ; every trigger zone of this quest (QuestKit fills it); disarmed by the ending

; The race guards (blocks.md): the choice (41, 42, 93) and the ending (90, 91, 93) each run once; check and set with no
; call between them.
Bool choiceTaken = False
Bool endTaken = False
Bool started = False ; character creation runs once, even if the quest were ever started again
Int marchWaits = 0

Event OnInit()
	; an update runs only in game mode, so the race menu opens once the hold around the marker is loaded
	RegisterForSingleUpdate(0.5)
EndEvent

Event OnUpdate()
	If !IsRunning()
		Return
	EndIf
	If GetStageDone(30) && !GetStageDone(32)
		StartMarch()
		Return
	EndIf
	If started || GetStageDone(10)
		Return
	EndIf
	started = True
	Actor player = Game.GetPlayer()
	Game.ForceThirdPerson()
	player.UnequipAll()
	player.RemoveAllItems()
	Game.PrecacheCharGen()
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	Game.ForceThirdPerson()
	SetStage(10)
EndEvent

; The walk starts in front of the player (E-package, start rule): stage 32 is set once the five walkers' 3D is loaded
; (the player has come out on the pier), checked once a second in game mode; after 60 checks it is set regardless.
Function StartMarch()
	marchWaits += 1
	If marchWaits >= 60 || (WuleenMarch.GetRef().Is3DLoaded() && UxMarch.GetRef().Is3DLoaded() && DivesMarch.GetRef().Is3DLoaded() && FindsMarch.GetRef().Is3DLoaded() && Courier.GetRef().Is3DLoaded())
		SetStage(32)
	Else
		RegisterForSingleUpdate(1.0)
	EndIf
EndFunction

; A walker the player overtook is put at the fire before the strike (it happens where the player stands).
Function AtFire(ReferenceAlias walker, Float dx, Float dy)
	ObjectReference r = walker.GetRef()
	If r.GetDistance(FireMark) > 400.0
		r.MoveTo(FireMark, dx, dy)
	EndIf
EndFunction

; Every zone of the quest off (the ending), so none can set a stage of the stopped quest.
Function DisarmZones()
	Int i = 0
	While i < Zones.Length
		Zones[i].Disable()
		i += 1
	EndWhile
EndFunction

; Wuleen-Sei has read the roll (the answers are offered after it).
Function ReadRoll()
	RollRead.SetValue(1)
EndFunction

; One answer given (the broker's line reads Answered): the hold's door opens (stage 20).
Function Answer()
	Answered.SetValue(1)
	SetStage(20)
EndFunction

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; the answer: the stair door unlocked, E-stage
	HoldDoor.Lock(False)
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; out of the hold (the door, TR-activate): the march copies on, the hold's people off (one of each
	; person); the walk waits for the player on the pier (StartMarch)
	MarchParent.Enable()
	HoldParent.Disable()
	CrewParent.Disable()
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
	marchWaits = 0
	RegisterForSingleUpdate(1.0)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_32
Function Fragment_32() ; hidden: the walkers loaded with the player; the march package (gated 32 to 40) starts, E-package
	HoldParent.Disable()
	CrewParent.Disable()
	WuleenMarch.GetActorRef().EvaluatePackage()
	UxMarch.GetActorRef().EvaluatePackage()
	DivesMarch.GetActorRef().EvaluatePackage()
	FindsMarch.GetActorRef().EvaluatePackage()
	Courier.GetActorRef().EvaluatePackage()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; E-enable (the camp), E-stage
	CampOrderly.Enable()
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; the strike: E-enable, the courier killed, E-move (the two witnesses), E-package (the leader goes)
	AtFire(WuleenMarch, 120.0, 60.0)
	AtFire(UxMarch, -120.0, 60.0)
	AtFire(DivesMarch, 100.0, -120.0)
	AtFire(FindsMarch, -100.0, -120.0)
	AtFire(Courier, 0.0, 160.0)
	CampAttacked.Enable()
	CellParent.Enable()
	CampOrderly.Disable()
	HoldParent.Disable()
	Actor c = Courier.GetActorRef()
	Courier.Clear()
	c.Kill(Leader.GetActorRef())
	SalSei.GetRef().MoveTo(ShedMark)
	DeeshDuun.GetRef().MoveTo(HutsMark)
	Leader.GetActorRef().EvaluatePackage()
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

; The one not reached dies in the fire; the leader is gone; the cutters stay at the shed until the ending disables them (CellParent).
Function Choose(ReferenceAlias lost, ObjectReference otherZone, ReferenceAlias saved, Int objective)
	Shore93Parent.Disable()
	otherZone.Disable()
	Actor a = lost.GetActorRef()
	lost.Clear()
	a.Kill()
	Leader.GetRef().Disable()
	saved.GetActorRef().EvaluatePackage()
	SetObjectiveCompleted(40)
	SetObjectiveDisplayed(objective)
EndFunction

;BEGIN FRAGMENT Fragment_41
Function Fragment_41()
	Bool first = !choiceTaken
	choiceTaken = True
	If first && !GetStageDone(42) && !GetStageDone(93)
		Choose(DeeshDuun, HutsZone, SalSei, 41)
	EndIf
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_42
Function Fragment_42()
	Bool first = !choiceTaken
	choiceTaken = True
	If first && !GetStageDone(41) && !GetStageDone(93)
		Choose(SalSei, ShedZone, DeeshDuun, 42)
	EndIf
EndFunction
;END FRAGMENT

; The endings' world (e-sal, e-deesh, e-alone): the aftermath, the survivors and Ties on the shore, the barge and the
; broker gone; TR-chain to MQ03 at 10; the quest's end.
Function Ending(ReferenceAlias saved, Int objective)
	CampAftermath.Enable()
	CampAttacked.Disable()
	CellParent.Disable()
	SurvivorsParent.Enable()
	Ties.GetRef().Enable()
	CrewParent.Disable()
	BrokerParent.Disable()
	WuleenMarch.GetRef().Disable()
	UxMarch.GetRef().Disable()
	If saved
		saved.GetRef().MoveTo(ShoreMark)
	EndIf
	SetObjectiveCompleted(objective)
	DisarmZones()
	NextQuest.SetStage(10)
	Stop()
EndFunction

;BEGIN FRAGMENT Fragment_90
Function Fragment_90() ; e-sal: the flag (E-global), the reed-knife (E-item)
	Bool first = !endTaken
	endTaken = True
	If first && !GetStageDone(91) && !GetStageDone(93)
		SavedSal.SetValue(1)
		Game.GetPlayer().AddItem(ReedKnife, 1)
		Ending(SalSei, 41)
	EndIf
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; e-deesh
	Bool first = !endTaken
	endTaken = True
	If first && !GetStageDone(90) && !GetStageDone(93)
		SavedDeesh.SetValue(1)
		Ending(DeeshDuun, 42)
	EndIf
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_93
Function Fragment_93() ; e-alone: the fire takes both
	Bool first = !endTaken
	endTaken = True
	If first && !choiceTaken && !GetStageDone(41) && !GetStageDone(42)
		choiceTaken = True
		Actor s = SalSei.GetActorRef()
		Actor d = DeeshDuun.GetActorRef()
		SalSei.Clear()
		DeeshDuun.Clear()
		s.Kill()
		d.Kill()
		Leader.GetRef().Disable()
		SetObjectiveCompleted(40)
		Ending(None, 40)
	EndIf
EndFunction
;END FRAGMENT

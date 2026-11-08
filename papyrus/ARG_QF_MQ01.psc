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

; The race guards (blocks.md): the choice (41, 42, 93) and the ending (90, 91, 93) each run once; check and set with no
; call between them.
Bool choiceTaken = False
Bool endTaken = False

Event OnInit()
	; an update runs only in game mode, so the race menu opens once the hold around the marker is loaded
	RegisterForSingleUpdate(0.5)
EndEvent

Event OnUpdate()
	If !IsRunning() || GetStageDone(10)
		Return
	EndIf
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

; Wuleen-Sei has read the roll (the answers are offered after it).
Function ReadRoll()
	RollRead.SetValue(1)
EndFunction

; One answer given (the broker's line reads Answered): the hold's door opens (stage 20).
Function Answer()
	Answered.SetValue(1)
	SetStage(20)
EndFunction

; The gang's packages read the stage.
Function March()
	WuleenMarch.TryToEvaluatePackage()
	UxMarch.TryToEvaluatePackage()
	DivesMarch.TryToEvaluatePackage()
	FindsMarch.TryToEvaluatePackage()
	Courier.TryToEvaluatePackage()
EndFunction

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; the answer: the stair door unlocked, E-stage
	HoldDoor.Lock(False)
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; out of the hold (the door, TR-activate): the gang sets off along the dock, E-package
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
	March()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_35
Function Fragment_35() ; the camp's edge (hidden): the gang at the fire before the player, E-move
	WuleenMarch.GetRef().MoveTo(FireMark, 120.0, 60.0)
	UxMarch.GetRef().MoveTo(FireMark, -120.0, 60.0)
	DivesMarch.GetRef().MoveTo(FireMark, 100.0, -120.0)
	FindsMarch.GetRef().MoveTo(FireMark, -100.0, -120.0)
	Courier.GetRef().MoveTo(FireMark, 0.0, 160.0)
	March()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; E-enable (the camp, the march), E-stage
	CampOrderly.Enable()
	MarchParent.Enable()
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; the strike: E-enable, the courier killed, E-move (the two witnesses), E-package (the leader goes)
	CampAttacked.Enable()
	CellParent.Enable()
	CampOrderly.Disable()
	HoldParent.Disable()
	Actor c = Courier.GetActorRef()
	Courier.Clear()
	c.Kill(Leader.GetActorRef())
	SalSei.GetRef().MoveTo(ShedMark)
	DeeshDuun.GetRef().MoveTo(HutsMark)
	Leader.TryToEvaluatePackage()
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

; The one not reached dies in the fire; the leader is gone; the cutters walk to the water's edge.
Function Choose(ReferenceAlias lost, ObjectReference otherZone, ReferenceAlias saved, Int objective)
	Shore93Parent.Disable()
	otherZone.Disable()
	Actor a = lost.GetActorRef()
	lost.Clear()
	a.Kill()
	Leader.GetRef().Disable()
	Cutter1.TryToEvaluatePackage()
	Cutter2.TryToEvaluatePackage()
	saved.TryToEvaluatePackage()
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

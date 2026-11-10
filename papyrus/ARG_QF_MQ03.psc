Scriptname ARG_QF_MQ03 extends Quest Hidden
{MQ03 A Dead Prisoner's Use (quest.main.mq03), started by MQ01's endings at 10: the camp at dawn, the Reed's house in
Lilmoth, the dream in the empty hold. Stage fragments and the helpers the lines call; shapes from Phase 3's blocks.}

ObjectReference Property JarParent Auto
ObjectReference Property ReedParent Auto
ObjectReference Property SurvivorsParent Auto
ObjectReference Property DreamParent Auto
ObjectReference Property BrokerParent Auto
ObjectReference Property HouseMark Auto
ObjectReference Property MatMark Auto
ObjectReference Property DreamMark Auto
ObjectReference Property HoldDoor Auto
Key Property HouseKey Auto
MiscObject Property Phial Auto
MiscObject Property Gold001 Auto
Faction Property VeiledReed Auto
GlobalVariable Property ReedSworn Auto
GlobalVariable Property ReedDeclined Auto
GlobalVariable Property AttackTold Auto
GlobalVariable Property NightTold Auto
GlobalVariable Property HistHearing Auto
ReferenceAlias Property Ties Auto
Quest[] Property Deferred Auto ; BM&V's greeting quest and Valenwood's start quests, held back until this quest ends
ObjectReference Property HouseDoor Auto ; the Reed's house's outer door (locked to its key until the player is inside)
ObjectReference[] Property Zones Auto ; every trigger zone of this quest (QuestKit fills it); disarmed by the ending
Quest Property NextQuest Auto ; ARG_MQ04 when it is in the plugin, else None

Bool houseTaken = False
Bool dreamStarted = False
Bool dreamTaken = False
Bool endTaken = False

; The attack told (E-global); the phial handed to Nesh-Deeka when carried.
Function TellAttack(ObjectReference akSpeaker, Bool phialCarried)
	AttackTold.SetValue(1)
	If phialCarried
		Game.GetPlayer().RemoveItem(Phial, 1, False, akSpeaker)
	EndIf
EndFunction

Function TellNight()
	NightTold.SetValue(1)
EndFunction

Function TakeOath()
	ReedSworn.SetValue(1)
	SetStage(40)
EndFunction

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; E-enable (the sap, the trap, the picks; the Reed's strangers), E-stage
	JarParent.Enable()
	ReedParent.Enable()
	SetObjectiveDisplayed(10)
	SetObjectiveDisplayed(11)
	SetObjectiveDisplayed(12)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_11
Function Fragment_11() ; the taste (TR-activate); a phial with Alchemy 25 (C-skill, E-item)
	Actor player = Game.GetPlayer()
	SetObjectiveCompleted(10) ; the taste is the step; the phial is the optional part of it
	If player.GetActorValue("Alchemy") >= 25 && player.GetItemCount(Phial) == 0
		player.AddItem(Phial, 1)
	EndIf
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-move (the player and Ties to the house), E-global (the Hist step), E-enable
	Bool first = !houseTaken
	houseTaken = True
	If !first
		Return
	EndIf
	HouseDoor.Lock(False) ; the house stays open from here, on every path (the sworn ending's key is a token)
	Game.GetPlayer().MoveTo(HouseMark)
	Ties.GetRef().MoveTo(MatMark)
	If HistHearing.GetValue() < 1
		HistHearing.SetValue(1)
	EndIf
	SurvivorsParent.Disable()
	ReedParent.Disable()
	SetObjectiveCompleted(11)
	SetObjectiveCompleted(12)
	SetObjectiveDisplayed(20)
	SetObjectiveDisplayed(21)
	SetObjectiveDisplayed(22)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; the dream: E-enable, the hold door locked, E-move
	Bool first = !dreamStarted
	dreamStarted = True
	If !first
		Return
	EndIf
	DreamParent.Enable()
	HoldDoor.Lock()
	Game.GetPlayer().MoveTo(DreamMark)
	SetObjectiveCompleted(20)
	SetObjectiveCompleted(21)
	SetObjectiveCompleted(22)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_45
Function Fragment_45() ; the door-gap reached: 90 if sworn (C-global), else 91
	Bool first = !dreamTaken
	dreamTaken = True
	If first
		If ReedSworn.GetValue() == 1
			SetStage(90)
		Else
			SetStage(91)
		EndIf
	EndIf
EndFunction
;END FRAGMENT

Function Ending()
	Actor player = Game.GetPlayer()
	DreamParent.Disable()
	HoldDoor.Lock(False)
	player.MoveTo(HouseMark)
	Ties.GetRef().Disable()
	BrokerParent.Enable()
	Int i = 0
	While i < Deferred.Length
		Deferred[i].Start()
		i += 1
	EndWhile
	If NextQuest
		NextQuest.SetStage(10)
	EndIf
	SetObjectiveCompleted(40)
	HouseDoor.Lock(False)
	DisarmZones()
	Stop()
EndFunction
; Every zone of the quest off (the ending), so none can set a stage of the stopped quest.
Function DisarmZones()
	Int i = 0
	While i < Zones.Length
		Zones[i].Disable()
		i += 1
	EndWhile
EndFunction


;BEGIN FRAGMENT Fragment_90
Function Fragment_90() ; e-sworn: E-faction, E-item (gold, the house key)
	Bool first = !endTaken
	endTaken = True
	If first && !GetStageDone(91)
		Actor player = Game.GetPlayer()
		ReedSworn.SetValue(1)
		player.SetFactionRank(VeiledReed, 0)
		player.AddItem(Gold001, 100)
		player.AddItem(HouseKey, 1)
		Ending()
	EndIf
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; e-unsworn
	Bool first = !endTaken
	endTaken = True
	If first && !GetStageDone(90)
		ReedDeclined.SetValue(1)
		Ending()
	EndIf
EndFunction
;END FRAGMENT

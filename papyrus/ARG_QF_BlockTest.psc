Scriptname ARG_QF_BlockTest extends Quest Hidden
{Phase 3's test quest: every effect block once, in its own shape. Throwaway; the shapes are the templates.}

ReferenceAlias Property Keeper Auto
ReferenceAlias Property Walker Auto
ReferenceAlias Property ZoneA Auto
ReferenceAlias Property ZoneB Auto
ObjectReference Property StartMarker Auto
ObjectReference Property WalkerMarker Auto
ObjectReference Property TokenParent Auto
ObjectReference Property CrabParent Auto
Key Property ShipKey Auto
MiscObject Property Token Auto
MiscObject Property Gold001 Auto
GlobalVariable Property Standing Auto
Faction Property DockHands Auto
Scene Property TalkScene Auto
Quest Property EndQuest Auto

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; start-up stage: E-move (the player), E-stage
	Game.GetPlayer().MoveTo(StartMarker)
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-item (setDoorAccess), E-enable, E-regard
	Actor player = Game.GetPlayer()
	SetObjectiveCompleted(10)
	If player.GetItemCount(ShipKey) == 0
		player.AddItem(ShipKey, 1)
	EndIf
	TokenParent.Enable()
	Keeper.GetActorRef().SetRelationshipRank(player, 1)
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; E-global
	Standing.SetValue(1)
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-item (taken), E-faction
	Actor player = Game.GetPlayer()
	player.RemoveItem(Token, player.GetItemCount(Token))
	player.SetFactionRank(DockHands, 0)
	SetObjectiveCompleted(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_50
Function Fragment_50() ; E-move (an actor out of an unloaded cell), E-enable, E-scene
	ObjectReference w = Walker.GetRef()
	w.MoveTo(WalkerMarker)
	w.Enable()
	TalkScene.Start()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_60
Function Fragment_60() ; E-package (by the alias's package list, gated on this stage), E-enable (a hostile)
	Walker.GetActorRef().EvaluatePackage()
	CrabParent.Enable()
	SetObjectiveDisplayed(60)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_65
Function Fragment_65() ; E-stage
	SetObjectiveCompleted(60)
	SetObjectiveDisplayed(65)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_71
Function Fragment_71() ; the race: disable the other trigger first
	ZoneB.GetRef().Disable()
	SetStage(75)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_72
Function Fragment_72()
	ZoneA.GetRef().Disable()
	SetStage(75)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_75
Function Fragment_75()
	SetObjectiveCompleted(65)
	SetObjectiveDisplayed(75)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_80
Function Fragment_80()
	SetObjectiveCompleted(75)
	SetObjectiveDisplayed(80)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_90
Function Fragment_90() ; E-item (gold), TR-chain
	Game.GetPlayer().AddItem(Gold001, 10)
	SetObjectiveCompleted(80)
	EndQuest.Start()
	SetStage(100)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_100
Function Fragment_100()
	CompleteQuest()
	Stop()
EndFunction
;END FRAGMENT

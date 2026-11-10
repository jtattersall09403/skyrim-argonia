Scriptname ARG_QF_TG02 extends Quest Hidden
{TG02 The Drowned Lockbox (quest.tg.tg02): the stage fragments and the helpers its lines call. Shapes from Phase 3's blocks.}

ReferenceAlias Property BentSpine Auto
ReferenceAlias Property Neeta Auto
ReferenceAlias Property Okan Auto
ReferenceAlias Property Dar Auto
ObjectReference Property ClientsParent Auto
MiscObject Property Figurine Auto
Armor Property Charm Auto
Armor Property Beads Auto
MiscObject Property Gold001 Auto
AchievementsScript Property AchievementsQuest Auto

; Okan-Tei's claim bought for twenty gold, then his claim stage.
Function PayOkan()
	Game.GetPlayer().RemoveItem(Gold001, 20)
	SetStage(22)
EndFunction

; All three pledges to one client for eighty gold, then the ending.
Function HandOver(ObjectReference akSpeaker)
	Actor player = Game.GetPlayer()
	player.RemoveItem(Figurine, 1, False, akSpeaker)
	player.RemoveItem(Charm, 1, False, akSpeaker)
	player.RemoveItem(Beads, 1, False, akSpeaker)
	player.AddItem(Gold001, 80)
	(akSpeaker as Actor).SetRelationshipRank(player, 1)
	SetStage(90)
EndFunction

; One pledge sold back to the one who claimed it for fifty gold; its stage counts the sales.
Function SellBack(ObjectReference akSpeaker, Int stage)
	Actor player = Game.GetPlayer()
	If stage == 43
		player.RemoveItem(Figurine, 1, False, akSpeaker)
	ElseIf stage == 44
		player.RemoveItem(Charm, 1, False, akSpeaker)
	Else
		player.RemoveItem(Beads, 1, False, akSpeaker)
	EndIf
	player.AddItem(Gold001, 50)
	(akSpeaker as Actor).SetRelationshipRank(player, -1)
	SetStage(stage)
EndFunction

; Three stages for one outcome: the check and the set have no call between them, so they are atomic (blocks.md).
Bool claimsTaken = False
Bool ended = False ; one ending only (90, 91 or 92)
Bool salesTaken = False
Function ClaimHeard()
	If !claimsTaken && GetStageDone(21) && GetStageDone(22) && GetStageDone(23)
		claimsTaken = True
		SetStage(40)
	EndIf
EndFunction
Function SaleMade()
	If !salesTaken && GetStageDone(43) && GetStageDone(44) && GetStageDone(45)
		salesTaken = True
		SetStage(91)
	EndIf
EndFunction

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-enable (the clients, the box, the house, the eels), E-stage
	ClientsParent.Enable()
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_21
Function Fragment_21()
	ClaimHeard()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_22
Function Fragment_22()
	ClaimHeard()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_23
Function Fragment_23()
	ClaimHeard()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40()
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(40)
	SetObjectiveDisplayed(41)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_43
Function Fragment_43()
	SaleMade()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_44
Function Fragment_44()
	SaleMade()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_45
Function Fragment_45()
	SaleMade()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_90
Function Fragment_90()
	If ended
		Return
	EndIf
	ended = True
	SetObjectiveCompleted(40)
	SetObjectiveCompleted(41)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; E-regard: Bent-Spine thinks better of the player
	If ended
		Return
	EndIf
	ended = True
	SetObjectiveCompleted(40)
	SetObjectiveCompleted(41)
	BentSpine.GetActorRef().SetRelationshipRank(Game.GetPlayer(), 1)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92() ; the failed ending: the stage's Fail Quest log entry, then Stop()
	If ended
		Return
	EndIf
	ended = True
	BentSpine.GetActorRef().SetRelationshipRank(Game.GetPlayer(), -1)
	Stop()
EndFunction
;END FRAGMENT

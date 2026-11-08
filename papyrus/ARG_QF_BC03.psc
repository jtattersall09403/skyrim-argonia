Scriptname ARG_QF_BC03 extends Quest Hidden
{BC03 The Broker's Mercy (quest.bc.bc03): stage fragments from Phase 3's proven shapes.}

ReferenceAlias Property Broker Auto
ReferenceAlias Property CrewBoss Auto
MiscObject Property Tokens Auto
MiscObject Property Gold001 Auto
GlobalVariable Property ChainbreakersStanding Auto
AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

; The race guard (blocks.md): one ending only; the check and the set have no call between them.
Bool ended = False

;BEGIN FRAGMENT Fragment_10
Function Fragment_10()
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; with the crew
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; with the broker
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_90
Function Fragment_90()
	If ended
		Return
	EndIf
	ended = True
	Actor player = Game.GetPlayer()
	player.RemoveItem(Tokens, player.GetItemCount(Tokens))
	Broker.GetActorRef().SetRelationshipRank(player, -1)
	ChainbreakersStanding.Mod(10)
	SetObjectiveCompleted(20)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91()
	If ended
		Return
	EndIf
	ended = True
	Actor player = Game.GetPlayer()
	player.AddItem(Gold001, 100)
	CrewBoss.GetActorRef().SetRelationshipRank(player, -1)
	SetObjectiveCompleted(30)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92()
	If ended
		Return
	EndIf
	ended = True
	Actor player = Game.GetPlayer()
	player.RemoveItem(Gold001, 50)
	player.AddItem(Gold001, 100)
	CrewBoss.GetActorRef().SetRelationshipRank(player, -1)
	SetObjectiveCompleted(30)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_94
Function Fragment_94()
	If ended
		Return
	EndIf
	ended = True
	SetObjectiveCompleted(10)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT


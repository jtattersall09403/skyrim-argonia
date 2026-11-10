Scriptname ARG_QF_LQ25 extends Quest Hidden
{LQ25 The River Monster (quest.local.lq25): stage fragments from Phase 3's proven shapes.}

ReferenceAlias Property Steerer Auto
ReferenceAlias Property Captain Auto
ObjectReference Property CrocParent Auto
MiscObject Property BaitBucket Auto
MiscObject Property Gold001 Auto
AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

; The race guard (blocks.md): one ending only.
Bool ended = False

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-enable (the crocodile and the bucket), E-stage
	CrocParent.Enable()
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-stage
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; the bucket shown to the captain: E-item (bucket taken, 60 gold), E-regard
	If ended
		Return
	EndIf
	ended = True
	CrocParent.Disable() ; the ending's disableRef ref.lq25.beast
	Actor player = Game.GetPlayer()
	player.RemoveItem(BaitBucket, player.GetItemCount(BaitBucket))
	player.AddItem(Gold001, 60)
	Captain.GetActorRef().SetRelationshipRank(player, 1)
	Steerer.GetActorRef().SetRelationshipRank(player, -1)
	SetObjectiveCompleted(40)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92() ; the crew's price: E-item (40 gold), E-regard
	If ended
		Return
	EndIf
	ended = True
	CrocParent.Disable() ; the ending's disableRef ref.lq25.beast
	Actor player = Game.GetPlayer()
	player.AddItem(Gold001, 40)
	Steerer.GetActorRef().SetRelationshipRank(player, 1)
	SetObjectiveCompleted(40)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

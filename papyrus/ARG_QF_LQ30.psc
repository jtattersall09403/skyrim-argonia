Scriptname ARG_QF_LQ30 extends Quest Hidden
{LQ30 The Gates of Helstrom (quest.local.lq30): stage fragments from Phase 3's proven shapes.}

ReferenceAlias Property Kin Auto
ReferenceAlias Property Youth Auto
ObjectReference Property ViperParent Auto
ObjectReference Property GateMarker Auto
ObjectReference Property GateZone Auto
MiscObject Property Gold001 Auto
AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

; The race guard (blocks.md): one ending only; the check and the set have no call between them.
Bool ended = False

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; E-enable (the viper and Sei-Wan), E-stage
	ViperParent.Enable()
	SetObjectiveDisplayed(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-stage
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; back at the gate without a word: E-move
	If ended
		Return
	EndIf
	ended = True
	Youth.GetRef().MoveTo(GateMarker)
	SetObjectiveCompleted(40)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92() ; talked home: E-move, E-item (60 gold), E-regard
	If ended
		Return
	EndIf
	ended = True
	Actor player = Game.GetPlayer()
	GateZone.Disable()
	Youth.GetRef().MoveTo(GateMarker)
	player.AddItem(Gold001, 60)
	Kin.GetActorRef().SetRelationshipRank(player, 1)
	Youth.GetActorRef().SetRelationshipRank(player, -1)
	SetObjectiveCompleted(40)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_93
Function Fragment_93() ; Sei-Wan dead: E-enable (the viper off)
	If ended
		Return
	EndIf
	ended = True
	GateZone.Disable()
	ViperParent.Disable()
	SetObjectiveCompleted(30)
	SetObjectiveCompleted(40)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

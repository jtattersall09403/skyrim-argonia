Scriptname ARG_QF_TG01 extends Quest Hidden
{TG01 A Dry Hand in a Wet City (quest.tg.tg01): the stage fragments and the helpers its lines call. Shapes from Phase 3's blocks.}

ObjectReference[] Property Zones Auto ; every trigger zone of this quest (QuestKit fills it); disarmed by the ending

; Every zone of the quest off (the ending), so none can set a stage of the stopped quest.
Function DisarmZones()
	Int i = 0
	While i < Zones.Length
		Zones[i].Disable()
		i += 1
	EndWhile
EndFunction

; The race guard (blocks.md): one ending only; the check and the set have no call between them.
Bool ended = False

ReferenceAlias Property Tilts Auto
ReferenceAlias Property Thief Auto
ObjectReference Property RoundParent Auto
Armor Property Necklace Auto
MiscObject Property Gold001 Auto
MiscObject Property Lockpick Auto
Faction Property Chapter Auto
Quest Property NextQuest Auto
AchievementsScript Property AchievementsQuest Auto

; Sits-By-The-Water's answer bought with a drink (E-item gold), then stage 30.
Function PayFriend()
	Game.GetPlayer().RemoveItem(Gold001, 10)
	SetStage(30)
EndFunction

; Keeps-What-Floats hands the necklace over, talked out of it (price 0) or bought (E-item).
Function NecklaceFrom(ObjectReference akSpeaker, Int price)
	Actor player = Game.GetPlayer()
	If price > 0
		player.RemoveItem(Gold001, price)
		akSpeaker.AddItem(Gold001, price)
	EndIf
	akSpeaker.RemoveItem(Necklace, 1, True, player)
EndFunction

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-enable (the thief, his friend, the Chapter), E-stage
	RoundParent.Enable()
	If Thief.GetRef().GetItemCount(Necklace) == 0
		Thief.GetRef().AddItem(Necklace, 1)
	EndIf
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30()
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
	SetObjectiveDisplayed(31)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-item (taken, paid, three picks), E-regard
	Actor player = Game.GetPlayer()
	player.RemoveItem(Necklace, 1, False, Tilts.GetRef())
	player.AddItem(Gold001, 100)
	player.AddItem(Lockpick, 3)
	Tilts.GetActorRef().SetRelationshipRank(player, 1)
	SetObjectiveCompleted(30)
	SetObjectiveCompleted(31)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_41
Function Fragment_41() ; E-item (taken, three picks, no pay), E-regard
	Actor player = Game.GetPlayer()
	player.RemoveItem(Necklace, 1, False, Tilts.GetRef())
	player.AddItem(Lockpick, 3)
	Tilts.GetActorRef().SetRelationshipRank(player, -1)
	SetObjectiveCompleted(30)
	SetObjectiveCompleted(31)
	SetObjectiveDisplayed(41) ; the record's second way down (the dock thief dead)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_90
Function Fragment_90() ; E-faction, TR-chain (TG02 at 20), the side quest's end
	If ended
		Return
	EndIf
	ended = True
	Game.GetPlayer().SetFactionRank(Chapter, 0)
	SetObjectiveCompleted(40)
	NextQuest.SetStage(20)
	DisarmZones()
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
	Game.GetPlayer().SetFactionRank(Chapter, 0)
	SetObjectiveCompleted(41)
	NextQuest.SetStage(20)
	DisarmZones()
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

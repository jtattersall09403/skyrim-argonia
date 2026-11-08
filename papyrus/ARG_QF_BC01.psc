Scriptname ARG_QF_BC01 extends Quest Hidden
{BC01 Four Months for a Boat (quest.bc.bc01): stage fragments from Phase 3's proven shapes.}

ReferenceAlias Property Patron Auto
ReferenceAlias Property Debtor Auto
ReferenceAlias Property Chest Auto
Book Property DebtBook Auto
ObjectReference Property BlackroseMarker Auto
ObjectReference Property ChannelEndZone Auto
MiscObject Property Gold001 Auto
GlobalVariable Property ChainbreakersStanding Auto
AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

; The race guard (blocks.md): one ending only; the check and the set have no call between them.
Bool ended = False

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; the book into the steward's chest (E-item); Never-Sold's sandbox at the landing runs from here
	If Chest.GetRef().GetItemCount(DebtBook) == 0
		Chest.GetRef().AddItem(DebtBook, 1)
	EndIf
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; she follows the player by her alias package
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_90
Function Fragment_90() ; her page torn out, the first price left in the chest, she goes to Blackrose
	If ended
		Return
	EndIf
	ended = True
	Actor player = Game.GetPlayer()
	player.RemoveItem(DebtBook, player.GetItemCount(DebtBook))
	Chest.GetRef().AddItem(Gold001, 100)
	Debtor.GetRef().MoveTo(BlackroseMarker)
	ChainbreakersStanding.Mod(10)
	SetObjectiveCompleted(10)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; she is gone down the channel
	If ended
		Return
	EndIf
	ended = True
	Debtor.GetRef().Disable(True)
	ChainbreakersStanding.Mod(10)
	SetObjectiveCompleted(40)
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

Scriptname ARG_QF_BlockTestEnd extends Quest Hidden
{Phase 3's second test quest (TR-chain): its completing stage counts on the Stats page as vanilla side quests do.}

AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; the journal lists a quest by its objectives
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_100
Function Fragment_100() ; Complete Quest flag on the stage; IncSideQuests() is Game.IncrementStat("Side Quests Completed")
	SetObjectiveCompleted(10)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction
;END FRAGMENT

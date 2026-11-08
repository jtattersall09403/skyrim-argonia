Scriptname ARG_QF_BC02 extends Quest Hidden
{BC02 One Out of the Smoke (quest.bc.bc02): stage fragments from Phase 3's proven shapes.}

ObjectReference Property SmokeParent Auto
ObjectReference Property SpeakerParent Auto
ObjectReference Property KillerParent Auto
ObjectReference Property MotherParent Auto
GlobalVariable Property ChainbreakersStanding Auto
AchievementsScript Property AchievementsQuest Auto ; Skyrim.esm AchievementsQuest

; The race guards (blocks.md): one choice, one ending; each check and set has no call between them.
Bool chosen = False
Bool ended = False

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; the smoke and the three held (E-enable)
	SmokeParent.Enable()
	SpeakerParent.Enable()
	KillerParent.Enable()
	MotherParent.Enable()
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30()
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_31
Function Fragment_31() ; Says-It-Plain chosen; the fire takes the other two
	If chosen
		Return
	EndIf
	chosen = True
	KillerParent.Disable()
	MotherParent.Disable()
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(31)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_32
Function Fragment_32() ; Hides-In-Reeds chosen
	If chosen
		Return
	EndIf
	chosen = True
	SpeakerParent.Disable()
	MotherParent.Disable()
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(32)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_33
Function Fragment_33() ; Keeps-The-Old-Count chosen
	If chosen
		Return
	EndIf
	chosen = True
	SpeakerParent.Disable()
	KillerParent.Disable()
	SetObjectiveCompleted(30)
	SetObjectiveDisplayed(33)
EndFunction
;END FRAGMENT

Function End(Int objective)
	SmokeParent.Disable()
	SetObjectiveCompleted(objective)
	AchievementsQuest.IncSideQuests()
	Stop()
EndFunction

;BEGIN FRAGMENT Fragment_91
Function Fragment_91()
	If ended
		Return
	EndIf
	ended = True
	ChainbreakersStanding.Mod(10)
	End(31)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92()
	If ended
		Return
	EndIf
	ended = True
	ChainbreakersStanding.Mod(10)
	End(32)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_93
Function Fragment_93()
	If ended
		Return
	EndIf
	ended = True
	ChainbreakersStanding.Mod(10)
	End(33)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_94
Function Fragment_94()
	If ended
		Return
	EndIf
	ended = True
	End(30)
EndFunction
;END FRAGMENT

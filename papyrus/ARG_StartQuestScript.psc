Scriptname ARG_StartQuestScript extends Quest
{ARG_Opening (PLAN Phase 1, the start): MQ101's stage 0 (ARG_QF_MQ101) has put the player on our marker in Lilmoth and
started this quest; here character creation, then the prisoner's clothes, third person and the journal line, as LAL's
chargen stage does it (ShowRaceMenu, then SetStage). Engine glue only.}

ObjectReference Property StartMarker Auto
Armor Property Tunic Auto
Armor Property Footwraps Auto

Event OnInit()
	; an update runs only in game mode, so the race menu opens once the cell around the marker is loaded
	RegisterForSingleUpdate(0.5)
EndEvent

Event OnUpdate()
	If GetStageDone(10)
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Game.ForceThirdPerson()
	Game.PrecacheCharGen()
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	Game.ForceThirdPerson() ; the race menu leaves the camera as it found it; the game starts in third person (owner)
	SetStage(10)
EndEvent

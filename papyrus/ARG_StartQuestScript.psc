Scriptname ARG_StartQuestScript extends Quest
{ARG_Opening (PLAN Phase 1, the start): a new game goes to our marker in Lilmoth, then character creation, then the
prisoner's clothes and the journal line. Started by MQ101's stage 0 (ARG_QF_MQ101). Engine glue only.}

ObjectReference Property StartMarker Auto
Armor Property Tunic Auto
Armor Property Footwraps Auto

Event OnInit()
	; The quest can start before the player is in the world; an update runs only in game mode, so the work waits for it.
	RegisterForSingleUpdate(0.1)
EndEvent

Event OnUpdate()
	If GetStageDone(10)
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Game.DisablePlayerControls()
	Game.FadeOutGame(True, True, 0.0, 0.5)
	player.MoveTo(StartMarker)
	player.RemoveAllItems()
	Game.FadeOutGame(False, True, 0.5, 1.0)
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	SetStage(10)
	Game.EnablePlayerControls()
EndEvent

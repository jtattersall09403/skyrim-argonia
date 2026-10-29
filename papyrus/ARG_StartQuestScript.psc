Scriptname ARG_StartQuestScript extends Quest
{Decision 0012 §1: a new game goes to black, then to the holding cell. Engine glue only: no rule lives here.}

ObjectReference Property HoldingMarker Auto

Event OnInit()
	; A start-game-enabled quest can see OnInit twice; stage 10 marks the move as done.
	If GetStageDone(10)
		Return
	EndIf
	SetStage(10)
	Game.DisablePlayerControls()
	Game.FadeOutGame(False, True, 4.0, 1.0) ; black now, fading back in after the move has loaded
	Game.GetPlayer().MoveTo(HoldingMarker)
	Utility.Wait(1.0)
	Game.EnablePlayerControls()
EndEvent

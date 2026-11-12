Scriptname ARG_QF_MQ101 extends Quest Hidden
{MQ101's fragment script in Argonia.esp's override of MQ101. The engine starts MQ101 on a new game, and the player is
in no cell until MQ101's stage 0 moves them: Live Another Life's stage-0 fragment does Player.MoveTo(NewStartMarker) and
then starts its chargen quest (qf_mq101_0003372b.psc, Fragment_332), and so do we (decision 0034). Here the move is to the
start marker in the barge hold and character creation runs once, in game mode, from OnUpdate. MQ01 starts with the new
game (Start Game Enabled), so nothing is started from here.}

ObjectReference Property StartMarker Auto
Armor Property Tunic Auto ; the roughspun tunic (03C9FE)
Armor Property Footwraps Auto ; the footwraps (03CA00)

; The new world's own start: with ArgoniaNewWorld.esm in the load order (the New World card) a new game begins at its
; ArgoniaNWStartMarker (0x802) and ANW_TravelGive (0x090000, tools/newworld/idspace.py row travel-give) runs character
; creation and puts the "Argonia Travel" power on the shout button, instead of the Lilmoth opening.
Int Property NWMarkerId = 0x802 AutoReadOnly
Int Property NWGiveId = 0x90000 AutoReadOnly

Bool started = False

;BEGIN FRAGMENT Fragment_0
Function Fragment_0()
	Actor player = Game.GetPlayer()
	player.RemoveAllItems()
	ObjectReference nwMarker = Game.GetFormFromFile(NWMarkerId, "ArgoniaNewWorld.esm") as ObjectReference
	ANW_TravelGive nwGive = Game.GetFormFromFile(NWGiveId, "ArgoniaNewWorld.esm") as ANW_TravelGive
	If nwMarker && nwGive
		player.MoveTo(nwMarker)
		nwGive.BeginNewGame()
		Stop()
		Return
	EndIf
	player.MoveTo(StartMarker)
	RegisterForSingleUpdate(0.5)
EndFunction
;END FRAGMENT

; Character creation, once, after the move: the race menu is refused in a fragment but runs from an update event.
Event OnUpdate()
	If started
		Return
	EndIf
	started = True
	Actor player = Game.GetPlayer()
	Game.ForceThirdPerson()
	player.UnequipAll()
	player.RemoveAllItems()
	Game.PrecacheCharGen()
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	Game.ForceThirdPerson()
	Stop()
EndEvent

Scriptname ARG_QF_MQ101 extends Quest Hidden
{MQ101's fragment script in Argonia.esp's override of MQ101. The engine starts MQ101 on a new game, and the player is
in no cell until MQ101's stage 0 moves them: Live Another Life's stage-0 fragment does Player.MoveTo(NewStartMarker) and
then starts its chargen quest (qf_mq101_0003372b.psc, Fragment_332), and so do we (decision 0034). ARG_MQ01 then
opens the race menu in the barge hold.}

Quest Property StartQuest Auto ; ARG_MQ01, the opening (MainQuest.cs)
ObjectReference Property StartMarker Auto

; The new world's own start: with ArgoniaNewWorld.esm in the load order (the New World card) a new game begins at its
; ArgoniaNWStartMarker (0x802) and ANW_TravelGive (0x00F000, seeded in newworld/sources/world_formids.json) runs character
; creation and puts the "Argonia Travel" power on the shout button, instead of the Lilmoth opening.
Int Property NWMarkerId = 0x802 AutoReadOnly
Int Property NWGiveId = 0xF000 AutoReadOnly

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
	StartQuest.Start()
	Stop()
EndFunction
;END FRAGMENT

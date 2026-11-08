Scriptname ARG_QF_MQ101 extends Quest Hidden
{MQ101's fragment script in Argonia.esp's override of MQ101. The engine starts MQ101 on a new game, and the player is
in no cell until MQ101's stage 0 moves them: Live Another Life's stage-0 fragment does Player.MoveTo(NewStartMarker) and
then starts its chargen quest (qf_mq101_0003372b.psc, Fragment_332), and so do we (decision 0034). ARG_MQ01 then
opens the race menu in the barge hold.}

Quest Property StartQuest Auto ; ARG_MQ01, the opening (MainQuest.cs)
ObjectReference Property StartMarker Auto

;BEGIN FRAGMENT Fragment_0
Function Fragment_0()
	Actor player = Game.GetPlayer()
	player.RemoveAllItems()
	player.MoveTo(StartMarker)
	StartQuest.Start()
	Stop()
EndFunction
;END FRAGMENT

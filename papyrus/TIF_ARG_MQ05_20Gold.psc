Scriptname TIF_ARG_MQ05_20Gold extends TopicInfo Hidden
{MQ05's line that sets stage 20: the TR-topic shape (BlockTest's TIF_ARG_BT_20).}

MiscObject Property Gold001 Auto
;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	Game.GetPlayer().RemoveItem(Gold001, 40)
	GetOwningQuest().SetStage(20)
EndFunction
;END FRAGMENT

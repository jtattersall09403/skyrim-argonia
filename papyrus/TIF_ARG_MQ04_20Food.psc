Scriptname TIF_ARG_MQ04_20Food extends TopicInfo Hidden
{MQ04's line that sets stage 20: the TR-topic shape (BlockTest's TIF_ARG_BT_20).}

Ingredient Property Salt Auto
;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	Game.GetPlayer().RemoveItem(Salt, 2)
	GetOwningQuest().SetStage(20)
EndFunction
;END FRAGMENT

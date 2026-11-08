Scriptname TIF_ARG_MQ04_40 extends TopicInfo Hidden
{MQ04's line that sets stage 40: the TR-topic shape (BlockTest's TIF_ARG_BT_20).}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	GetOwningQuest().SetStage(40)
EndFunction
;END FRAGMENT

Scriptname TIF_ARG_MQ05_20 extends TopicInfo Hidden
{MQ05's line that sets stage 20: the TR-topic shape (BlockTest's TIF_ARG_BT_20).}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	GetOwningQuest().SetStage(20)
EndFunction
;END FRAGMENT

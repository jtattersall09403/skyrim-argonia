Scriptname TIF_ARG_LQ30_30 extends TopicInfo Hidden
{LQ30: the topic that sets stage 30 (TR-topic).}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	GetOwningQuest().SetStage(30)
EndFunction
;END FRAGMENT

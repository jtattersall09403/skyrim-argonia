Scriptname TIF_ARG_LQ25_20 extends TopicInfo Hidden
{LQ25: the topic that sets stage 20 (TR-topic).}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	GetOwningQuest().SetStage(20)
EndFunction
;END FRAGMENT

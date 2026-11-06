Scriptname TIF_ARG_BT_50 extends TopicInfo Hidden
{ARG_BlockTest's keeper line that sets stage 50: the TR-topic shape (Phase 3). Throwaway; the shape is the template.}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	GetOwningQuest().SetStage(50)
EndFunction
;END FRAGMENT

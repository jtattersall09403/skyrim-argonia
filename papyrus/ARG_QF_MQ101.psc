Scriptname ARG_QF_MQ101 extends Quest Hidden
{MQ101's fragment script in Argonia.esp's override of MQ101. The engine starts MQ101 on a new game; its stage 0 starts
our opening instead of Helgen and stops MQ101, the way Live Another Life diverts the start (decision 0034).}

Quest Property ARGOpening Auto

;BEGIN FRAGMENT Fragment_0
Function Fragment_0()
	ARGOpening.Start()
	Stop()
EndFunction
;END FRAGMENT

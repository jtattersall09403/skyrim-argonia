Scriptname ARG_QF_MQ05 extends Quest Hidden
{MQ05 Helstrom Behind Its Marsh (tools/ArgoniaPlugin/MQ05.cs): stage fragments, each a proven block shape.}

ReferenceAlias Property KaskaMeen Auto
ReferenceAlias Property EiTuja Auto
ObjectReference Property WayParent Auto
GlobalVariable Property MindersHold Auto
GlobalVariable Property NisswoRead Auto

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; E-stage: the Reed's word
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-enable: the wasps of the way
	SetObjectiveCompleted(10)
	WayParent.Enable()
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-stage: tell one of them
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; ending: told the tree-minder (E-global)
	SetObjectiveCompleted(40)
	MindersHold.SetValue(1)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92() ; ending: told the Nisswo (E-global)
	SetObjectiveCompleted(40)
	NisswoRead.SetValue(1)
EndFunction
;END FRAGMENT

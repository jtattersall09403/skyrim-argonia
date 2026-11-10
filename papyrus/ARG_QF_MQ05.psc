Scriptname ARG_QF_MQ05 extends Quest Hidden
{MQ05 Helstrom Behind Its Marsh (tools/ArgoniaPlugin/MQ05.cs): stage fragments, each a proven block shape.}

ObjectReference[] Property Zones Auto ; every trigger zone of this quest (QuestKit fills it); disarmed by the ending

; The race guard (blocks.md): one ending only; the check and the set have no call between them.
Bool ended = False

; Every zone of the quest off (the ending), so none can set a stage of the stopped quest.
Function DisarmZones()
	Int i = 0
	While i < Zones.Length
		Zones[i].Disable()
		i += 1
	EndWhile
EndFunction


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
	If ended
		Return
	EndIf
	ended = True
	SetObjectiveCompleted(40)
	MindersHold.SetValue(1)
	DisarmZones()
	Stop()
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_92
Function Fragment_92() ; ending: told the Nisswo (E-global)
	If ended
		Return
	EndIf
	ended = True
	SetObjectiveCompleted(40)
	NisswoRead.SetValue(1)
	DisarmZones()
	Stop()
EndFunction
;END FRAGMENT

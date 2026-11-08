Scriptname ARG_QF_MQ04 extends Quest Hidden
{MQ04 The Tree That Turned Its Face (tools/ArgoniaPlugin/MQ04.cs): stage fragments, each a proven block shape.}

ReferenceAlias Property RootHerald Auto
ReferenceAlias Property PaysLate Auto
ObjectReference Property CampParent Auto
ObjectReference Property WithdrawnParent Auto
ObjectReference Property ReconciledParent Auto
ObjectReference Property ReturnParent Auto
MiscObject Property SapJars Auto
GlobalVariable Property Reconciled Auto
GlobalVariable Property Adopted Auto
GlobalVariable Property Standing Auto
Faction Property LowReedVillage Auto
Quest Property NextQuest Auto

;BEGIN FRAGMENT Fragment_10
Function Fragment_10() ; E-stage: the root-herald's leave
	SetObjectiveDisplayed(10)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_20
Function Fragment_20() ; E-stage: down to the roots
	SetObjectiveCompleted(10)
	SetObjectiveDisplayed(20)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_30
Function Fragment_30() ; E-stage: Pays-Late or the egg-tender
	SetObjectiveCompleted(20)
	SetObjectiveDisplayed(30)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_40
Function Fragment_40() ; E-enable: the cell's camp (review F5)
	SetObjectiveCompleted(30)
	CampParent.Enable()
	SetObjectiveDisplayed(40)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_45
Function Fragment_45() ; E-enable: the leeches of the way back (review F2)
	SetObjectiveCompleted(40)
	ReturnParent.Enable()
	SetObjectiveDisplayed(45)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_91
Function Fragment_91() ; ending e-minder: E-item, E-global, E-enable, E-faction, then MQ05
	Actor player = Game.GetPlayer()
	SetObjectiveCompleted(45)
	player.RemoveItem(SapJars, player.GetItemCount(SapJars))
	Reconciled.SetValue(1)
	Adopted.SetValue(1)
	Standing.SetValue(Standing.GetValue() + 10)
	ReconciledParent.Enable()
	WithdrawnParent.Disable()
	CampParent.Disable()
	player.SetFactionRank(LowReedVillage, 0)
	NextQuest.SetStage(10)
EndFunction
;END FRAGMENT

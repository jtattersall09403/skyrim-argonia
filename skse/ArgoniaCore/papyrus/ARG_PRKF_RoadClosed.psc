;The closed road's perk fragment (2.W3; tools/argonia_world/routes/infra.py): ARG_Perk_RoadClosed's Activate entry
;point (Run Immediately, Replace Default) on an exit gate (keyword ARG_ClosedGate) shows ARG_Msg_RoadClosed, "The
;road beyond is closed." No rule: the text is the MESG record's. Papyrus only because the engine runs perk entry
;fragments from scripts.
Scriptname ARG_PRKF_RoadClosed Extends Perk Hidden

Message Property RoadClosed Auto

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
  RoadClosed.Show()
;END CODE
EndFunction
;END FRAGMENT

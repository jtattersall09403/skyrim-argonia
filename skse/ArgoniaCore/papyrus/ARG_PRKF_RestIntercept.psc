;The rest intercept's perk fragments (native map P3; 1.5): ARG_Perk_RestIntercept's Activate entry points (Run
;Immediately, Replace Default) on an ARG_RestSpot (a camp spot) and on the ARG_VasteiPile. One native call each: the
;rest, the sitting and the pile are ArgoniaCore's. Papyrus only because the engine runs perk entry fragments from
;scripts; the notification is the refusal line ArgoniaCore words.
Scriptname ARG_PRKF_RestIntercept Extends Perk Hidden

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
  If !ArgoniaCore.RestAt(akTargetRef)
    Debug.Notification(ArgoniaCore.RestNotice())
  EndIf
;END CODE
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_1
Function Fragment_1(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
  ArgoniaCore.TakeVastei(akTargetRef)
;END CODE
EndFunction
;END FRAGMENT

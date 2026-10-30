;The dialogue intercept's perk fragment (native map P3; 1.3 §b): ARG_Perk_DialogueIntercept's Activate entry point
;(Run Immediately, Replace Default) on an ARG_Speaker runs this instead of the vanilla Talk. One native call: the
;conversation is ArgoniaCore's. Papyrus only because the engine runs perk entry fragments from scripts.
Scriptname ARG_PRKF_DialogueIntercept Extends Perk Hidden

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
  ArgoniaCore.OpenDialogue(akTargetRef)
;END CODE
EndFunction
;END FRAGMENT

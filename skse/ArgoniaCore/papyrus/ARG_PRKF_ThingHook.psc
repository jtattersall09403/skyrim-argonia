;A quest thing's activate hook (1.4; tools/argonia_world/thing_hooks.py): ARG_Perk_ThingHooks's Activate entry point
;(Run Immediately, Replace Default, "Examine") on a thing's activator (keyword ARG_ThingHook). One native call: which
;flag the thing sets is ArgoniaCore's thing table. Papyrus only because the engine runs perk entry fragments from
;scripts.
Scriptname ARG_PRKF_ThingHook Extends Perk Hidden

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akTargetRef, Actor akActor)
;BEGIN CODE
  ArgoniaCore.ThingActivated(akTargetRef)
;END CODE
EndFunction
;END FRAGMENT

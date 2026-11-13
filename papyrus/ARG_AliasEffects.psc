Scriptname ARG_AliasEffects extends ReferenceAlias Hidden
{A quest form's rows run on one event of the alias's reference (ARG_Effects; docs/design/quest-form.md). On says which,
as vanilla's set-stage scripts hook them: 0 its death (the mortal watch, a who-must-live window, a death trigger with an
until); 1 the player takes it (defaultSetStageOnPlayerAcquire's OnContainerChanged); 2 the player activates it
(defaultSetStageAliasScript's OnActivate); 3 it is read (defaultSetStageOnCloseBook's OnRead). The rows guard
themselves, so an event that comes again does nothing again.}

Int[] Property Op Auto
Form[] Property What Auto
Float[] Property Num Auto
Int Property On = 0 Auto

Event OnDeath(Actor akKiller)
	If On == 0
		ARG_Effects.Run(Op, What, Num, 0, Op.Length, GetOwningQuest(), GetReference())
	EndIf
EndEvent

Event OnContainerChanged(ObjectReference akNewContainer, ObjectReference akOldContainer)
	If On == 1 && akNewContainer == Game.GetPlayer()
		ARG_Effects.Run(Op, What, Num, 0, Op.Length, GetOwningQuest(), GetReference())
	EndIf
EndEvent

Event OnActivate(ObjectReference akActionRef)
	If On == 2 && akActionRef == Game.GetPlayer()
		ARG_Effects.Run(Op, What, Num, 0, Op.Length, GetOwningQuest(), GetReference())
	EndIf
EndEvent

Event OnRead()
	If On == 3
		ARG_Effects.Run(Op, What, Num, 0, Op.Length, GetOwningQuest(), GetReference())
	EndIf
EndEvent

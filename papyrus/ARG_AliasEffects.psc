Scriptname ARG_AliasEffects extends ReferenceAlias Hidden
{The mortal watch's script on each person a main or faction quest cannot go on without (ARG_MortalWatch, always
running; docs/design/quest-form.md). When the person dies it runs its rows once (ARG_Effects): while their quest has
not ended, the message box that the story can no longer be finished; then their quest's failed ending, only if that
quest is running.}

Int[] Property Op Auto
Form[] Property What Auto
Float[] Property Num Auto

Event OnDeath(Actor akKiller)
	ARG_Effects.Run(Op, What, Num, 0, Op.Length, GetOwningQuest(), GetReference())
EndEvent

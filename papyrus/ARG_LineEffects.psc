Scriptname ARG_LineEffects extends TopicInfo Hidden
{The one response script of every line of a quest built from a quest form (docs/design/quest-form.md). Op, What and
Num are the line's rows (ARG_Effects); Owner is the form's quest, whose stages the rows set. A line that opens a
person's force-greet runs its rows as it begins (so the greeting is not offered twice); every other line runs them as
it ends. A line with no rows carries the script for Line (the form's line id) and Written alone, which the plugin
reader reads; nothing reads them in game.}

Int[] Property Op Auto
Form[] Property What Auto
Float[] Property Num Auto
Quest Property Owner Auto
String Property Line Auto
Bool Property Written Auto

;BEGIN FRAGMENT Fragment_Begin
Function Fragment_Begin(ObjectReference akSpeakerRef)
	ARG_Effects.Run(Op, What, Num, 0, Op.Length, Owner, akSpeakerRef)
EndFunction
;END FRAGMENT

;BEGIN FRAGMENT Fragment_End
Function Fragment_End(ObjectReference akSpeakerRef)
	ARG_Effects.Run(Op, What, Num, 0, Op.Length, Owner, akSpeakerRef)
EndFunction
;END FRAGMENT

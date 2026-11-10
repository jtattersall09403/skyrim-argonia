Scriptname TIF_ARG_BoatTravel extends TopicInfo Hidden
{A boatman's travel line: one script for every boatman and destination, set by each line's properties
(the destination's marker and the fare), as vanilla's carriage takes the fare and fast-travels the player.}

ObjectReference Property Destination Auto
{where the boat lands: the destination place's map marker or landing}
Int Property Fare Auto
{gold, fixed per destination}
MiscObject Property Gold001 Auto
{Skyrim.esm 00000F}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	Actor player = Game.GetPlayer()
	If player.GetItemCount(Gold001) < Fare
		Return
	EndIf
	player.RemoveItem(Gold001, Fare)
	Game.FastTravel(Destination)
EndFunction
;END FRAGMENT

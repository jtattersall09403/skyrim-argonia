Scriptname TIF_ARG_NoSurrender extends TopicInfo Hidden
{Native law's resist line: the player refuses the Owing and resists arrest, and the place's guards take no surrender.
Vanilla's resist line runs the guard's SetPlayerResistingArrest(), after which a guard takes the player's yield. Here
the place's guard faction also becomes the player's enemy, as vanilla's civil war makes a side's soldiers the
player's enemies (Faction.SetPlayerEnemy): an enemy fights on, so the fight runs to its end.}

Faction Property Guards Auto
{the place's guard faction: its guards alone, never the townsfolk of the crime faction}

;BEGIN FRAGMENT Fragment_0
Function Fragment_0(ObjectReference akSpeakerRef)
	(akSpeakerRef as Actor).SetPlayerResistingArrest()
	Guards.SetPlayerEnemy(true)
EndFunction
;END FRAGMENT

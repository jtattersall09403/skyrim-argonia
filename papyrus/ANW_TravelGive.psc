Scriptname ANW_TravelGive extends Quest
{ANW_TravelGive (ArgoniaNewWorld.esm, start game enabled): gives the player the lesser power "Argonia Travel", on a new game and on any save the plugin joins. Engine glue only.}

Spell Property Power Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	If !player.HasSpell(Power)
		player.AddSpell(Power, False)
	EndIf
EndEvent

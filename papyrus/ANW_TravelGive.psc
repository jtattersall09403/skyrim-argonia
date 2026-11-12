Scriptname ANW_TravelGive extends Quest
{ANW_TravelGive (ArgoniaNewWorld.esm, start game enabled): gives the player the lesser power "Argonia Travel" (any new game, and any save the plugin joins) and runs the new world's own start: ARG_QF_MQ101 (Argonia.esp) puts a new game's player on ArgoniaNWStartMarker and calls BeginNewGame, which opens character creation, dresses the player and puts the power on the shout button. Engine glue only.}

Spell Property Power Auto
Armor Property Tunic Auto
Armor Property Footwraps Auto

Event OnInit()
	Actor player = Game.GetPlayer()
	If !player.HasSpell(Power)
		player.AddSpell(Power, False)
	EndIf
EndEvent

Function BeginNewGame()
	; an update runs only in game mode, so the race menu opens once the cell around the marker is loaded
	RegisterForSingleUpdate(0.5)
EndFunction

Event OnUpdate()
	Actor player = Game.GetPlayer()
	Game.ForceThirdPerson()
	player.UnequipAll()
	player.RemoveAllItems()
	Game.PrecacheCharGen()
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	If !player.HasSpell(Power)
		player.AddSpell(Power, False)
	EndIf
	player.EquipSpell(Power, 2) ; slot 2 is the voice slot: the shout button casts the power
	Game.ForceThirdPerson()
EndEvent

Scriptname ARG_StartQuestScript extends Quest
{ARG_Opening (PLAN Phase 1, the start): MQ101's stage 0 (ARG_QF_MQ101) has put the player on our marker in Lilmoth and
started this quest; here character creation, then the prisoner's clothes, third person and the journal line, as LAL's
chargen stage does it (ShowRaceMenu, then SetStage). Engine glue only.}

ObjectReference Property StartMarker Auto
Armor Property Tunic Auto
Armor Property Footwraps Auto
; TEST KIT for the walk phases (owner, 2026-11-06); removed with the authored opening (Phase 3)
Weapon Property TestWeapon Auto
Armor Property TestShield Auto
Spell[] Property TestSpells Auto

Event OnInit()
	; an update runs only in game mode, so the race menu opens once the cell around the marker is loaded
	RegisterForSingleUpdate(0.5)
EndEvent

Event OnUpdate()
	If GetStageDone(10)
		Return
	EndIf
	Actor player = Game.GetPlayer()
	Game.ForceThirdPerson()
	; a bare head in the race menu: the Player NPC's default outfit (Skyrim.esm ArmorIronAllOutfit, iron helmet among it)
	; is put on once the player's 3D loads, after MQ101's stage-0 RemoveAllItems, so strip again here, in game mode,
	; before the menu (vanilla MQ101 and LAL undress the player before ShowRaceMenu)
	player.UnequipAll()
	player.RemoveAllItems()
	Game.PrecacheCharGen()
	Game.ShowRaceMenu()
	Utility.Wait(0.1) ; game time only: returns after the race menu closes
	player.AddItem(Tunic, 1, True)
	player.AddItem(Footwraps, 1, True)
	player.EquipItem(Tunic, False, True)
	player.EquipItem(Footwraps, False, True)
	; TEST KIT (walk phases only): a one-handed weapon, a shield and Magic Expanded spells
	player.AddItem(TestWeapon, 1, True)
	player.AddItem(TestShield, 1, True)
	Int i = 0
	While i < TestSpells.Length
		player.AddSpell(TestSpells[i], False)
		i += 1
	EndWhile
	Game.ForceThirdPerson() ; the race menu leaves the camera as it found it; the game starts in third person (owner)
	SetStage(10)
	; the Quests menu lists an active quest only once an objective shows (owner walk 2026-11-07)
	SetObjectiveDisplayed(10)
EndEvent

Scriptname ARG_Effects Hidden
{The quest form's results, carried out row by row (docs/design/quest-form.md, "How a form becomes records").
A row is one entry of three parallel arrays: Op (what to do), What (the form it acts on) and Num (its number).
Run does the rows from index From up to, not including, To, in order. Every operation is short and safe to repeat:
a row that has already happened does nothing again. Nothing here waits, polls or keeps a state.
The operation numbers are QuestForm.cs's (tools/ArgoniaPlugin); a number not listed is never written.}

; ---- the quest's own steps
;  1 SetStage           Num: a stage of this quest, set unless it is already done
;  2 ShowObjective      Num: an objective of this quest, shown unless it is completed
;  3 CompleteObjective  Num: completed, if it is shown
;  4 FailObjective      Num: failed, if it is shown and not completed
;  5 SetActive          this quest becomes the tracked one
;  6 StopQuest          this quest stops (the last row of an ending)
;  7 IncSideQuests      What: Skyrim.esm's AchievementsQuest; "Side Quests Completed" on the Stats page
;  8 FailIfDead         What: a person who must live; Num: the failed ending, set if they are dead (the other rows are skipped)
;  9 SetStageIfRunning  What: a quest; Num: its stage, set only while that quest runs and has not done it
; 10 IfStageDone        What: a quest; Num: a stage; guards the next row: it runs only if that stage is done
; 11 IfQuestOpen        What: a quest; guards the next row: it runs only if that quest has not ended
; 13 IfStageAtMost      What: a quest; Num: a stage; guards the next row: it runs only if the quest's stage is at most that
; 14 IfHolds            What: an item; Num: a count; guards the next row: it runs only if the player holds that many
; 15 CompleteAll        Num: the highest objective; every objective up to it that is shown and open is completed, in order
; 16 FailAll            Num: the highest objective; every objective up to it that is shown and open is failed, in order
;                       (guards stand in a row before the one row they guard: one that fails skips the rest and that row)
; 12 StartOnStage       What: a quest started by this stage; Num: the stage it starts at
; ---- the form's results
; 20 GiveItem  21 TakeItem   What: the item; Num: how many
; 22 GiveGold  23 TakeGold   What: Gold001; Num: how much
; 24 SetNumber 25 AddNumber  What: the number's global; Num: the value
; 26 JoinFaction             What: the faction
; 27 SetRank                 What: the faction; Num: the rank (joining it first)
; 28 ChangeRegard            What: the person; Num: by how much (their relationship rank with the player, -4 to 4)
; 29 SwitchOn  30 SwitchOff  What: the reference
; 31 LockDoor  32 UnlockDoor What: the door
; 33 ShowMessage             What: the message box
; 34 SpeakerHostile          the person speaking the line attacks the player
; 35 StartQuest              What: the quest; Num: the stage it is set to
; 36 GiveOwnership           What: the reference (a container another owns); it and what it holds become the player's
; 37 TeachSpell  38 ForgetSpell  What: the spell (a spell, power or ability); the player learns or loses it
; 39 MakeEnemy   40 MakePeace    What: the faction; its people attack the player on sight, or no longer do
; 41 LeaveFaction               What: the faction; the player is no longer of it
; 42 AddPerk  43 RemovePerk     What: the perk; the player gains or loses it
; 44 MarkOnMap                  What: the map marker reference; it is shown on the map (fast travel once visited)
; 45 SetBounty                  What: the faction (a crime faction); Num: the bounty the player carries there, 0 clears it
; 46 OwnRoom                    What: the interior cell; the room and the unowned things in it become the player's
; 47 RaiseSkill                 Num: by + 100 * the skill's index in the form's skill list (see SkillName); the skill rises by `by`

Function Run(Int[] op, Form[] what, Float[] num, Int from, Int to, Quest q, ObjectReference speaker = None) Global
	Actor player = Game.GetPlayer()
	Quest x
	Actor a
	Int r
	Int i = from
	While i < to
		Int o = op[i]
		Form w = what[i]
		Int n = num[i] as Int
		If o == 1
			If !q.GetStageDone(n)
				q.SetStage(n)
			EndIf
		ElseIf o == 2
			If !q.IsObjectiveCompleted(n)
				q.SetObjectiveDisplayed(n)
			EndIf
		ElseIf o == 3
			If q.IsObjectiveDisplayed(n) && !q.IsObjectiveCompleted(n)
				q.SetObjectiveCompleted(n)
			EndIf
		ElseIf o == 15 || o == 16
			r = 0
			While r <= n
				If q.IsObjectiveDisplayed(r) && !q.IsObjectiveCompleted(r) && !q.IsObjectiveFailed(r)
					If o == 15
						q.SetObjectiveCompleted(r)
					Else
						q.SetObjectiveFailed(r)
					EndIf
				EndIf
				r += 1
			EndWhile
		ElseIf o == 4
			If q.IsObjectiveDisplayed(n) && !q.IsObjectiveCompleted(n) && !q.IsObjectiveFailed(n)
				q.SetObjectiveFailed(n)
			EndIf
		ElseIf o == 5
			q.SetActive()
		ElseIf o == 6
			q.Stop()
		ElseIf o == 7
			(w as AchievementsScript).IncSideQuests()
		ElseIf o == 8
			If (w as Actor).IsDead()
				If !q.GetStageDone(n)
					q.SetStage(n)
				EndIf
				Return
			EndIf
		ElseIf o == 9
			x = w as Quest
			If x.IsRunning() && !x.GetStageDone(n)
				x.SetStage(n)
			EndIf
		ElseIf o == 10 || o == 11 || o == 13 || o == 14
			x = w as Quest
			If (o == 10 && !x.GetStageDone(n)) || (o == 11 && (x.IsCompleted() || (x.IsStopped() && x.GetStage() > 0))) || (o == 13 && x.GetStage() > n) || (o == 14 && player.GetItemCount(w) < n)
				i += 1
				While i < to && (op[i] == 10 || op[i] == 11 || op[i] == 13 || op[i] == 14)
					i += 1
				EndWhile
			EndIf
		ElseIf o == 12 || o == 35
			x = w as Quest
			If !x.GetStageDone(n)
				x.SetStage(n)
			EndIf
		ElseIf o == 20
			player.AddItem(w, n)
		ElseIf o == 21 || o == 23
			player.RemoveItem(w, n)
		ElseIf o == 22
			player.AddItem(w, n)
		ElseIf o == 24
			(w as GlobalVariable).SetValue(num[i])
		ElseIf o == 25
			(w as GlobalVariable).Mod(num[i])
		ElseIf o == 26
			If !player.IsInFaction(w as Faction)
				player.AddToFaction(w as Faction)
			EndIf
		ElseIf o == 27
			If !player.IsInFaction(w as Faction)
				player.AddToFaction(w as Faction)
			EndIf
			player.SetFactionRank(w as Faction, n)
		ElseIf o == 28
			a = w as Actor
			r = a.GetRelationshipRank(player) + n
			If r > 4
				r = 4
			ElseIf r < -4
				r = -4
			EndIf
			a.SetRelationshipRank(player, r)
		ElseIf o == 29
			(w as ObjectReference).Enable()
		ElseIf o == 30
			(w as ObjectReference).Disable()
		ElseIf o == 31
			(w as ObjectReference).Lock(true)
		ElseIf o == 32
			(w as ObjectReference).Lock(false)
		ElseIf o == 33
			(w as Message).Show()
		ElseIf o == 36
			(w as ObjectReference).SetActorOwner(player.GetActorBase())
		ElseIf o == 37
			player.AddSpell(w as Spell)
		ElseIf o == 38
			player.RemoveSpell(w as Spell)
		ElseIf o == 39 || o == 40
			(w as Faction).SetPlayerEnemy(o == 39)
		ElseIf o == 41
			player.RemoveFromFaction(w as Faction)
		ElseIf o == 42
			player.AddPerk(w as Perk)
		ElseIf o == 43
			player.RemovePerk(w as Perk)
		ElseIf o == 44
			(w as ObjectReference).AddToMap(false)
		ElseIf o == 45
			(w as Faction).SetCrimeGold(n)
		ElseIf o == 46
			(w as Cell).SetActorOwner(player.GetActorBase())
		ElseIf o == 47
			Game.IncrementSkillBy(SkillName(n / 100), n % 100)
		ElseIf o == 34
			a = speaker as Actor
			If a && !a.IsDead()
				a.StartCombat(player)
			EndIf
		EndIf
		i += 1
	EndWhile
EndFunction

; The skill a RaiseSkill row names, as Skyrim's skill functions call it: the form's skill list, in its order.
String Function SkillName(Int i) Global
	If i == 0
		Return "Speechcraft"
	ElseIf i == 1
		Return "Sneak"
	ElseIf i == 2
		Return "Lockpicking"
	ElseIf i == 3
		Return "Pickpocket"
	ElseIf i == 4
		Return "Alchemy"
	ElseIf i == 5
		Return "OneHanded"
	ElseIf i == 6
		Return "TwoHanded"
	ElseIf i == 7
		Return "Marksman"
	ElseIf i == 8
		Return "Block"
	ElseIf i == 9
		Return "HeavyArmor"
	ElseIf i == 10
		Return "LightArmor"
	ElseIf i == 11
		Return "Smithing"
	ElseIf i == 12
		Return "Enchanting"
	ElseIf i == 13
		Return "Alteration"
	ElseIf i == 14
		Return "Conjuration"
	ElseIf i == 15
		Return "Destruction"
	ElseIf i == 16
		Return "Illusion"
	EndIf
	Return "Restoration"
EndFunction

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
; 10 IfStageDone        What: a quest; Num: a stage; the next row runs only if that stage is done
; 11 IfQuestOpen        What: a quest; the next row runs only if that quest has not ended
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
		ElseIf o == 10
			If !(w as Quest).GetStageDone(n)
				i += 1
			EndIf
		ElseIf o == 11
			x = w as Quest
			If x.IsCompleted() || (x.IsStopped() && x.GetStage() > 0)
				i += 1
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
		ElseIf o == 34
			a = speaker as Actor
			If a && !a.IsDead()
				a.StartCombat(player)
			EndIf
		EndIf
		i += 1
	EndWhile
EndFunction

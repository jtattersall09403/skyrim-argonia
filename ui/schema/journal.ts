// The journal (1.2 §c, 1.4, 1.12 §6): our paper book. Four ribbons: Current (the quests under way, grouped by
// questline or place from the quest records), Finished (done and failed, the failed marked), All entries (the dated
// diary) and Topics (2.12 fills it). A quest opens on its latest direction, then its dated entries. A typed search
// narrows the tab; ArgoniaCore filters (skse/core views::journal_state), the view only draws.
import { GameDate, runs } from "./common.ts";
import { enumDef, int, intent, list, oneOf, opt, push, ref, str, struct } from "./types.ts";

export const JournalTab = enumDef("JournalTab", "the ribbon the book is open at", ["current", "finished", "all", "topics"]);
// The names of skse/core/journal's Kind and Status.
export const JournalEntryKind = enumDef("JournalEntryKind", "what the entry records", ["progress", "complete", "fail"]);
export const QuestStatus = enumDef("QuestStatus", "a quest's standing in the index", ["active", "complete", "failed"]);
export const QuestGroupKind = enumDef("QuestGroupKind", "what a group of quests is named for (quest_line.group local: the place)",
  ["questline", "place"]);

export const JournalEntry = struct("JournalEntry", "One dated entry of the log", {
  quest: str("world db quest.id"),
  questName: str("the quest's name as the book heads it"),
  date: ref(GameDate),
  kind: oneOf(JournalEntryKind),
  runs: runs("the entry text, split at keyword spans (links join in 2.12)"),
});

export const QuestIndexItem = struct("QuestIndexItem", "One quest of a ribbon's list", {
  id: str("world db quest.id"),
  name: str("the quest's name"),
  status: oneOf(QuestStatus),
  started: ref(GameDate),
  last: ref(GameDate, "the date of its latest entry"),
});

export const QuestGroup = struct("QuestGroup", "The quests of one questline or one place, most recently written first", {
  label: str("the questline's or the place's name (the quest records)"),
  kind: oneOf(QuestGroupKind),
  quests: list(ref(QuestIndexItem)),
});

export const OpenQuest = struct("OpenQuest", "The quest the book is open at: its latest direction, then its entries", {
  id: str("world db quest.id"),
  name: str("the quest's name"),
  status: oneOf(QuestStatus),
  group: str("the questline or place it is listed under"),
  directions: opt(str("where to go next in words, never a marker (the latest stage's directions)")),
  entries: list(ref(JournalEntry), "its entries, newest first"),
});

export const journalState = push("journal.state", 2, "The open journal at one ribbon", {
  tab: oneOf(JournalTab),
  page: int("0-based page of the All entries diary", { min: 0 }),
  pageCount: int("pages of the diary", { min: 1 }),
  search: opt(str("the typed search the tab is narrowed by, as typed")),
  groups: list(ref(QuestGroup), "Current or Finished: the quests matching the search, by group"),
  quest: opt(ref(OpenQuest), "the quest opened from Current or Finished"),
  entries: list(ref(JournalEntry), "All entries: this page of the diary, oldest first"),
  matches: int("entries (All entries) or quests (Current, Finished) the search matched", { min: 0 }),
});

export const journalPage = intent("journal.page", 2, "A ribbon chosen, a page turned, a quest opened or the search typed", {
  tab: oneOf(JournalTab),
  page: int("0-based diary page asked for", { min: 0 }),
  quest: opt(str("open this quest id (Current or Finished)")),
  search: opt(str("narrow the tab to entries and quests containing these words")),
});

export const messages = [journalState, journalPage];

// The journal (1.2 §c, 1.4): a Morrowind-style book of dated entries, the quest index, directions text. The topics
// index is 2.12's (a new tab, so a new version of journal.state).
import { GameDate, runs } from "./common.ts";
import { enumDef, int, intent, list, oneOf, opt, push, ref, str, struct } from "./types.ts";

export const JournalTab = enumDef("JournalTab", "the page set the book shows", ["entries", "quests"]);
// The names of skse/core/journal's Kind and Status.
export const JournalEntryKind = enumDef("JournalEntryKind", "what the entry records", ["progress", "complete", "fail"]);
export const QuestStatus = enumDef("QuestStatus", "a quest's standing in the index", ["active", "complete", "failed"]);

export const JournalEntry = struct("JournalEntry", "One dated entry of the log", {
  quest: str("world db quest.id"),
  questName: str("the quest's name as the book heads it"),
  date: ref(GameDate),
  kind: oneOf(JournalEntryKind),
  runs: runs("the entry text, split at keyword spans (links join in 2.12)"),
});

export const QuestIndexItem = struct("QuestIndexItem", "One quest of the index", {
  id: str("world db quest.id"),
  name: str("the quest's name"),
  status: oneOf(QuestStatus),
  started: ref(GameDate),
  directions: opt(str("where to go next in words, never a marker (quest_stage_directions)")),
});

export const journalState = push("journal.state", 1, "The open journal at one page", {
  tab: oneOf(JournalTab),
  page: int("0-based page of the tab", { min: 0 }),
  pageCount: int("pages in the tab", { min: 1 }),
  questFilter: opt(str("the quest id the entries are filtered to")),
  entries: list(ref(JournalEntry), "this page's entries, oldest first"),
  quests: list(ref(QuestIndexItem), "the quest index, most recent first"),
});

export const journalPage = intent("journal.page", 1, "A page was turned, a tab chosen or a quest picked from the index", {
  tab: oneOf(JournalTab),
  page: int("0-based page asked for", { min: 0 }),
  questFilter: opt(str("filter the entries to this quest id")),
});

export const messages = [journalState, journalPage];

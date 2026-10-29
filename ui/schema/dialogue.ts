// The dialogue window (1.2 §b, 1.3 §b): Morrowind-style topics, hyperlinked keywords, persuasion, disposition.
import { runs } from "./common.ts";
import { bool, enumDef, int, intent, list, oneOf, opt, push, ref, str, struct } from "./types.ts";

export const DispositionBand = enumDef("DispositionBand", "the band the record's variant text keys on (core_disposition_band)",
  ["low", "mid", "high"]);

export const DialogueEntryKind = enumDef("DialogueEntryKind", "what put an entry in the window",
  ["greeting", "answer", "notice"]);

export const Speaker = struct("Speaker", "The person the player is talking to", {
  id: str("world db npc.id"),
  name: str("the name the player sees"),
});

export const DialogueEntry = struct("DialogueEntry", "One block of the scrolling conversation, oldest first", {
  kind: oneOf(DialogueEntryKind),
  heading: opt(str("the topic label asked, shown above an answer")),
  runs: runs("the text, split at keyword spans"),
});

export const TopicItem = struct("TopicItem", "One entry of the topic list", {
  id: str("world db topic.id"),
  label: str("the label the player clicks"),
});

export const Disposition = struct("Disposition", "Disposition as Morrowind shows it", {
  value: int("0..100", { min: 0, max: 100 }),
  band: oneOf(DispositionBand),
});

export const PersuasionOption = struct("PersuasionOption", "One persuasion action (admire, intimidate, taunt, bribe and our own)", {
  id: str("the action id; the set is ArgoniaCore's (2.5)"),
  label: str("the button text"),
  enabled: bool("false when the action cannot be taken now"),
  cost: opt(int("gold it spends (a bribe)", { min: 0 })),
});

export const Persuasion = struct("Persuasion", "The persuasion button and its actions", {
  available: bool("whether the button shows"),
  options: list(ref(PersuasionOption)),
});

export const dialogueState = push("dialogue.state", 1, "The whole dialogue window, sent on open and after every change", {
  speaker: ref(Speaker),
  entries: list(ref(DialogueEntry), "the conversation so far, oldest first"),
  topics: list(ref(TopicItem), "the topics this person can be asked, in display order"),
  disposition: ref(Disposition),
  persuasion: ref(Persuasion),
  canLeave: bool("whether Goodbye is offered (a forced conversation hides it)"),
});

export const dialogueTopic = intent("dialogue.topic", 1, "A topic in the list was chosen", {
  topic: str("world db topic.id"),
});

export const dialogueKeyword = intent("dialogue.keyword", 1, "A hyperlinked keyword in the text was clicked", {
  topic: str("world db topic.id the run carried"),
});

export const dialoguePersuade = intent("dialogue.persuade", 1, "A persuasion action was taken", {
  option: str("PersuasionOption.id"),
});

export const dialogueGoodbye = intent("dialogue.goodbye", 1, "Goodbye was chosen", {});

export const messages = [dialogueState, dialogueTopic, dialogueKeyword, dialoguePersuade, dialogueGoodbye];

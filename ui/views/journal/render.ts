// The journal (1.2 §c), render only: Morrowind's open book. The entries tab is a spread of dated entries (the page
// ArgoniaCore sent, flowing over both leaves); the quests tab is the index with each quest's directions in words.
// Page turns, tabs and a quest pick are journal.page intents; ArgoniaCore answers with the page.
import type { JournalEntry, JournalPage, JournalState, QuestIndexItem } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

const page = (b: JournalPage) => ({ type: "journal.page" as const, v: 1 as const, body: b });

const STATUS: Record<QuestIndexItem["status"], string> = { active: "", complete: "Finished", failed: "Failed" };

function entry(e: JournalEntry, prev: JournalEntry | undefined): string {
  const date = prev?.date.text === e.date.text ? "" : `<h2 class="date">${esc(e.date.text)}</h2>`;
  const runs = e.runs.map((r) => r.topic === undefined ? esc(r.text) : `<span class="kw">${esc(r.text)}</span>`).join("");
  return `<div class="entry ${e.kind}">${date}<p><span class="qname">${esc(e.questName)}.</span> ${runs}</p></div>`;
}

function quest(q: QuestIndexItem): string {
  const status = STATUS[q.status] ? `<span class="status">${STATUS[q.status]}</span>` : "";
  const dir = q.directions !== undefined ? `<p class="dir">${esc(q.directions)}</p>` : "";
  const name = intentButton(page({ tab: "entries", page: 0, questFilter: q.id }), "qlink",
    `${esc(q.name)}${status}`, `data-key="quest:${esc(q.id)}"`);
  return `<li class="quest ${q.status}">${name}<p class="since">Begun ${esc(q.started.text)}</p>${dir}</li>`;
}

export function render(s: JournalState): string {
  const tab = (t: JournalState["tab"], label: string) =>
    intentButton(page({ tab: t, page: 0 }), `tab${s.tab === t ? " on" : ""}`, label,
      `data-key="tab:${t}" aria-pressed="${s.tab === t}"`);
  const filter = s.questFilter !== undefined ? { questFilter: s.questFilter } : {};
  const prev = s.page > 0
    ? intentButton(page({ tab: s.tab, page: s.page - 1, ...filter }), "turn prev", "Previous", `data-key="prev"`)
    : `<span class="turn"></span>`;
  const next = s.page + 1 < s.pageCount
    ? intentButton(page({ tab: s.tab, page: s.page + 1, ...filter }), "turn next", "Next", `data-key="next"`)
    : `<span class="turn"></span>`;

  let leaves: string;
  if (s.tab === "entries") {
    const named = s.questFilter !== undefined ? s.quests.find((q) => q.id === s.questFilter)?.name : undefined;
    const head = s.questFilter !== undefined
      ? `<div class="filter">${esc(named ?? "One quest")}
         ${intentButton(page({ tab: "entries", page: 0 }), "showall", "Show every entry", `data-key="showall"`)}</div>`
      : "";
    const body = s.entries.length
      ? s.entries.map((e, i) => entry(e, s.entries[i - 1])).join("")
      : `<p class="empty">Nothing is written here yet.</p>`;
    leaves = `${head}<div class="flow">${body}</div>`;
  } else {
    leaves = s.quests.length
      ? `<ul class="index">${s.quests.map(quest).join("")}</ul>`
      : `<p class="empty">No quest has begun.</p>`;
  }
  return `<section class="book" aria-label="Journal">
  <div class="spread paper"><div class="spine"></div><div class="leaves">${leaves}</div></div>
  <nav class="foot">
    <div class="tabs">${tab("entries", "Journal")}${tab("quests", "Quests")}</div>
    <div class="pager">${prev}<span class="folio">${s.page + 1} of ${s.pageCount}</span>${next}</div>
    ${intentButton({ type: "view.close", v: 1, body: { view: "journal" } }, "close", "Close", `data-key="close"`)}
  </nav>
</section>`;
}

// The page-turn intents a key or pad shoulder sends: the same as the Previous and Next buttons.
export function turn(s: JournalState, dir: -1 | 1) {
  const p = s.page + dir;
  if (p < 0 || p >= s.pageCount) return null;
  return page({ tab: s.tab, page: p, ...(s.questFilter !== undefined ? { questFilter: s.questFilter } : {}) });
}

// The journal (1.2 §c, 1.12 §6), render only: our paper book inside a frame-style window. Four ribbons across the
// top: Current, Finished, All entries and Topics (2.12 fills it). Current and Finished list the quests by questline
// or place on the left leaf; the right leaf is the quest opened, its latest direction first, then its dated entries,
// newest first. All entries is the dated diary flowing over both leaves (main.ts turns the leaves). The search field
// narrows the ribbon; ArgoniaCore filters and answers with the state, the view only draws. No statistics page and no
// "show on map": the journal is words.
import type { JournalEntry, JournalPage, JournalState, OpenQuest, QuestGroup, QuestIndexItem } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export const page = (b: JournalPage) => ({ type: "journal.page" as const, v: 2 as const, body: b });

const RIBBONS: [JournalState["tab"], string][] =
  [["current", "Current"], ["finished", "Finished"], ["all", "All entries"], ["topics", "Topics"]];
const STATUS: Record<QuestIndexItem["status"], string> = { active: "", complete: "Finished", failed: "Failed" };

const withSearch = (s: JournalState) => (s.search !== undefined ? { search: s.search } : {});

function text(e: JournalEntry): string {
  return e.runs.map((r) => r.topic === undefined ? esc(r.text) : `<span class="kw">${esc(r.text)}</span>`).join("");
}

// A dated entry; the date is shown once for a run of entries on the same day.
function entry(e: JournalEntry, prev: JournalEntry | undefined, named: boolean): string {
  const date = prev?.date.text === e.date.text ? "" : `<h3 class="date">${esc(e.date.text)}</h3>`;
  const qname = named ? `<span class="qname">${esc(e.questName)}</span>` : "";
  const end = e.kind === "complete" ? ` <span class="end">Finished.</span>`
    : e.kind === "fail" ? ` <span class="end failed">Failed.</span>` : "";
  return `<div class="entry ${e.kind}">${date}<p>${qname}${text(e)}${end}</p></div>`;
}

function questRow(s: JournalState, q: QuestIndexItem): string {
  const open = s.quest?.id === q.id;
  const mark = STATUS[q.status] ? `<span class="status">${STATUS[q.status]}</span>` : "";
  return `<li class="quest ${q.status}${open ? " open" : ""}">${intentButton(
    page({ tab: s.tab, page: 0, quest: q.id, ...withSearch(s) }), "qlink",
    `<span class="qn">${esc(q.name)}</span>${mark}`, `data-key="quest:${esc(q.id)}" aria-pressed="${open}"`)}</li>`;
}

function group(s: JournalState, g: QuestGroup): string {
  return `<li class="group ${g.kind}"><h2 class="ghead">${esc(g.label)}</h2>
    <ul class="quests">${g.quests.map((q) => questRow(s, q)).join("")}</ul></li>`;
}

function opened(q: OpenQuest): string {
  const mark = STATUS[q.status] ? ` <span class="status">${STATUS[q.status]}</span>` : "";
  const dir = q.directions !== undefined
    ? `<div class="dir"><h3>Where next</h3><p>${esc(q.directions)}</p></div>` : "";
  const body = q.entries.map((e, i) => entry(e, q.entries[i - 1], false)).join("");
  return `<article class="qpage ${q.status}"><h2 class="qtitle">${esc(q.name)}${mark}</h2>
    <p class="under">${esc(q.group)}</p>${dir}${body}</article>`;
}

function empty(s: JournalState): string {
  if (s.search !== undefined) return `<p class="empty">No entry matches “${esc(s.search)}”.</p>`;
  switch (s.tab) {
    case "current": return `<p class="empty">No quest is under way.</p>`;
    case "finished": return `<p class="empty">No quest is finished yet.</p>`;
    case "all": return `<p class="empty">The journal has no entries yet.</p>`;
    default: return `<p class="empty">Topics you hear in conversation are listed here.</p>`;
  }
}

export function render(s: JournalState): string {
  const ribbons = RIBBONS.map(([t, label]) => intentButton(page({ tab: t, page: 0, ...withSearch(s) }),
    `ribbon${s.tab === t ? " on" : ""}`, label, `data-key="tab:${t}" aria-pressed="${s.tab === t}"`)).join("");
  // Each turn button is view-local (data-ui): main.ts turns a leaf, or sends the page intent it carries; with no
  // page that way it carries none and stays hidden unless main.ts finds a leaf to turn to.
  const turnButton = (dir: "prev" | "next", to: number, label: string) => {
    const attrs = `data-key="${dir}" data-ui="turn" data-dir="${dir}"`;
    return to >= 0 && to < s.pageCount
      ? intentButton(page({ tab: s.tab, page: to, ...withSearch(s) }), `turn ${dir}`, label, attrs)
      : `<button type="button" class="turn ${dir} none" ${attrs}>${label}</button>`;
  };
  const found = s.search !== undefined
    ? `<span class="found" aria-live="polite">${s.matches} found</span>${intentButton(page({ tab: s.tab, page: 0 }),
      "clear", "Clear", `data-key="search:clear"`)}` : "";
  const search = s.tab === "topics" ? "" : `<div class="search"><input type="text" class="sfield" data-nav
    data-key="search" spellcheck="false" autocomplete="off" placeholder="Search" value="${esc(s.search ?? "")}"
    aria-label="Search the journal">${found}</div>`;

  let leaves: string, pager = "";
  if (s.tab === "current" || s.tab === "finished") {
    const list = s.groups.length
      ? `<ul class="groups scroll" data-list="quests">${s.groups.map((g) => group(s, g)).join("")}</ul>` : empty(s);
    const right = s.quest ? opened(s.quest) : "";
    // The opened quest flows down its leaf into further leaves (one CSS column each), turned like the diary's.
    leaves = `<div class="leaf left">${list}</div><div class="leaf right"><div class="flow qflow">${right}</div></div>`;
    pager = `<div class="pager">${turnButton("prev", -1, "Previous")}<span class="folio"></span>${turnButton("next", -1, "Next")}</div>`;
  } else if (s.tab === "all") {
    const body = s.entries.length ? s.entries.map((e, i) => entry(e, s.entries[i - 1], true)).join("") : empty(s);
    leaves = `<div class="flow">${body}</div>`;
    pager = `<div class="pager">${turnButton("prev", s.page - 1, "Previous")}<span class="folio">${s.page + 1} of ${s.pageCount}</span>${turnButton("next", s.page + 1, "Next")}</div>`;
  } else {
    leaves = `<div class="leaf left">${empty(s)}</div><div class="leaf right"></div>`;
  }
  return `<section class="window journal" aria-label="Journal">
  <header class="bar"><h1>Journal</h1>${search}
    ${intentButton({ type: "view.close", v: 1, body: { view: "journal" } }, "close", "Close", `data-key="close"`)}</header>
  <nav class="ribbons">${ribbons}</nav>
  <div class="spread paper ${s.tab}"><div class="spine"></div><div class="leaves">${leaves}</div></div>
  ${pager}
</section>`;
}

// The page-turn intents a key or pad shoulder sends on the diary: the same as the Previous and Next buttons.
export function turn(s: JournalState, dir: -1 | 1) {
  if (s.tab !== "all") return null;
  const p = s.page + dir;
  if (p < 0 || p >= s.pageCount) return null;
  return page({ tab: s.tab, page: p, ...withSearch(s) });
}

// The search typed (or cleared): the same ribbon from its start, with the open quest kept.
export function searchIntent(s: JournalState, q: string) {
  const query = q.trim() === "" ? {} : { search: q };
  return page({ tab: s.tab, page: 0, ...(s.quest ? { quest: s.quest.id } : {}), ...query });
}

// The ribbon order the pad's shoulders walk outside the diary.
export function ribbonStep(s: JournalState, dir: -1 | 1) {
  const i = RIBBONS.findIndex(([t]) => t === s.tab) + dir;
  if (i < 0 || i >= RIBBONS.length) return null;
  return page({ tab: RIBBONS[i][0], page: 0, ...withSearch(s) });
}

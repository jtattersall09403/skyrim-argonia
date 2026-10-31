// Our HUD (1.2 §d), render only. Souls-style bars whose drawn length grows with the stat's maximum, the sneak eye,
// the effect stack, the vastei plaque, the place banner, the prompt with the glyph of the device in use, and the
// notice stack, and the minimap top right with its compass rose (1.12 §5; drawn by minimap.ts). No compass bar and no
// quest marker, ever. The HUD sends no intents.
import type { Bar, Effect, HudState, InputGlyph, Notice, PlaceBanner, Prompt } from "../../schema/generated/messages.ts";
import { esc } from "../core/html.ts";
import { ROSE } from "./minimap.ts";
import { PLAYER_SVG } from "../chart/render.ts";

// rem of bar per point of maximum, and the longest a bar may draw (the rest of the growth is CSS's max-width).
export const REM_PER_POINT = 0.1;
export const barLength = (b: Bar): number => Math.max(4, b.max * REM_PER_POINT);
export const fillPct = (b: Bar): number => (b.max <= 0 ? 0 : Math.min(100, Math.max(0, (100 * b.current) / b.max)));
// Health at or under this share of its maximum is the low-health state: the bar pulses and the screen's rim darkens.
export const LOW_HEALTH = 0.25;
export const isLow = (bars: Bar[]): boolean =>
  bars.some((b) => b.kind === "health" && b.shown && b.max > 0 && b.current / b.max <= LOW_HEALTH);

const BAR_NAME: Record<Bar["kind"], string> = {
  health: "Health", stamina: "Stamina", magicka: "Magicka", breath: "Breath", climb: "Grip",
};

// What the view remembers between pushes (main.ts keeps it): the damage trail's percentage per bar, and the bars
// now regenerating. The render stays a pure function of the push and this memory.
export interface BarMemory { trail: Partial<Record<Bar["kind"], number>>; regen: ReadonlySet<Bar["kind"]>; }
const NONE: BarMemory = { trail: {}, regen: new Set() };

// One step of that memory, pure: a drop leaves the trail at the highest value just held (Dark Souls' lag), a rise
// marks the bar regenerating, and a bar not drawn forgets. `last` is each bar's fill percentage at the last push.
export function remember(last: Partial<Record<Bar["kind"], number>>, bars: Bar[], mem: BarMemory):
  { last: Partial<Record<Bar["kind"], number>>; mem: BarMemory } {
  const nextLast: Partial<Record<Bar["kind"], number>> = {}, trail: BarMemory["trail"] = {}, regen = new Set<Bar["kind"]>();
  for (const b of bars) {
    if (!b.shown) continue;
    const f = fillPct(b), was = last[b.kind];
    nextLast[b.kind] = f;
    const held = mem.trail[b.kind];
    if (was !== undefined && f < was) trail[b.kind] = Math.max(held ?? was, was);
    else if (held !== undefined && held > f) trail[b.kind] = held;
    if (was !== undefined && f > was) regen.add(b.kind);
    else if (was !== undefined && f === was && mem.regen.has(b.kind)) regen.add(b.kind);
  }
  return { last: nextLast, mem: { trail, regen } };
}

// The three standing bars are known by colour and place, as in Dark Souls; breath and grip come and go, so they
// carry their name.
const NAMED = new Set<Bar["kind"]>(["breath", "climb"]);
const bar = (b: Bar, mem: BarMemory): string => {
  const f = fillPct(b), t = Math.max(f, mem.trail[b.kind] ?? f);
  const cls = [b.kind, mem.regen.has(b.kind) && f < 100 ? "regen" : "", b.kind === "health" && isLow([b]) ? "low" : ""]
    .filter(Boolean).join(" ");
  return `<div class="row ${b.kind}"><div class="bar ${cls}" style="width:${barLength(b).toFixed(2)}rem"
  role="meter" aria-label="${BAR_NAME[b.kind]}" aria-valuenow="${Math.round(b.current)}" aria-valuemax="${Math.round(b.max)}">
  <div class="trail" data-trail="${b.kind}" style="width:${t.toFixed(1)}%"></div><div class="fill" style="width:${f.toFixed(1)}%"></div></div>${NAMED.has(b.kind) ? `<span class="bar-name">${BAR_NAME[b.kind]}</span>` : ""}</div>`;
};

// The sneak eye, our own drawing: the lids part as detection rises; a word beside it for the folded phone.
export const sneakWord = (eye: number): string => (eye < 0.25 ? "Hidden" : eye < 0.75 ? "Watched" : "Seen");
function eye(open: number): string {
  const k = (1.5 + 7 * open).toFixed(2);
  return `<svg class="eye-svg" viewBox="-12 -10 24 20" aria-hidden="true">
    <path d="M-11 0 Q0 -${k} 11 0 Q0 ${k} -11 0Z" class="lid"/>
    <clipPath id="eyeclip"><path d="M-11 0 Q0 -${k} 11 0 Q0 ${k} -11 0Z"/></clipPath>
    <circle r="${(2 + 3 * open).toFixed(2)}" class="iris" clip-path="url(#eyeclip)"/></svg>`;
}

// Status symbols, our own minimal marks until the Fal-made set (0017 §5) is imported.
const SYMBOL: Record<string, string> = {
  "status.fortify": `<path d="M-5 3 L0 -3 L5 3" /><path d="M-5 7 L0 1 L5 7" />`,
  "status.disease": `<circle cx="-3" cy="-2" r="1.6"/><circle cx="3" cy="-1" r="1.2"/><circle cx="0" cy="3.5" r="1.8"/>`,
};
const symbol = (id: string): string => `<svg viewBox="-8 -8 16 16" aria-hidden="true">${SYMBOL[id] ?? `<path d="M0 -5 L5 0 L0 5 L-5 0Z"/>`}</svg>`;

export const timeLeft = (s: number): string => (s >= 90 ? `${Math.ceil(s / 60)} min` : `${Math.ceil(s)} s`);
const effect = (e: Effect): string => `<li class="fx ${e.polarity}" data-id="${esc(e.id)}">
  <span class="medal">${symbol(e.glyph)}</span><span class="fx-name">${esc(e.label)}</span>
  ${e.remaining !== undefined ? `<span class="fx-time">${timeLeft(e.remaining)}</span>` : ""}</li>`;

// Input glyphs: the installer extracts Skyrim's own button art (0017 §5); until then, and as the fallback, a keycap,
// a pad button and a touch ring drawn here. Each device's glyph is in the HTML; CSS shows the device in use.
export function glyph(g: InputGlyph): string {
  const id = g.glyph;
  const label = id.includes(".") ? id.slice(id.indexOf(".") + 1) : id;
  if (g.device === "touch") return `<span class="glyph touch" data-device="touch" data-glyph="${esc(id)}"><span class="ring"></span></span>`;
  const shape = g.device === "gamepad" ? "pad" : "key";
  return `<span class="glyph ${shape}" data-device="${g.device}" data-glyph="${esc(id)}">${esc(label)}</span>`;
}

const prompt = (p: Prompt): string => `<div class="prompt">${p.inputs.map(glyph).join("")}
  <span class="verb">${esc(p.verb)}</span><span class="target">${esc(p.target)}</span></div>`;

const banner = (b: PlaceBanner): string => `<div class="banner${b.firstVisit ? " first" : ""}" data-place="${esc(b.place)}">
  ${b.firstVisit ? `<div class="found">Discovered</div>` : ""}
  <div class="place">${esc(b.name)}</div>${b.region !== undefined ? `<div class="region">${esc(b.region)}</div>` : ""}</div>`;

const notice = (n: Notice): string => `<li class="notice ${n.kind}" data-id="${esc(n.id)}">${esc(n.text)}</li>`;

export function renderBars(bars: Bar[], mem: BarMemory = NONE): string {
  return bars.filter((b) => b.shown).map((b) => bar(b, mem)).join("");
}

// The vastei mark: our own drawing, a scale-plate lozenge with a centre line.
const VMARK = `<svg class="vmark" viewBox="-8 -10 16 20" aria-hidden="true"><path d="M0 -9 L7 0 L0 9 L-7 0Z"/><path d="M0 -5 L0 5"/></svg>`;

export function render(s: HudState, mem: BarMemory = NONE): string {
  if (!s.visible) return `<div class="hud hidden"></div>`;
  const sneak = s.sneak.sneaking
    ? `<div class="sneak" data-eye="${s.sneak.eye}">${eye(s.sneak.eye)}<span class="sneak-word">${sneakWord(s.sneak.eye)}</span></div>` : "";
  const gain = s.vastei.gained !== undefined && s.vastei.gained > 0 ? `<span class="gain">+${s.vastei.gained}</span>` : "";
  return `<div class="hud${isLow(s.bars) ? " low" : ""}">
  <div class="vignette" aria-hidden="true"></div>
  <div class="corner">
    <div class="bars" data-bars>${renderBars(s.bars, mem)}</div>
    <div class="vastei${gain ? " up" : ""}">${VMARK}<span class="count">${s.vastei.carried}</span><span class="vlabel">Vastei</span>${gain}</div>
    ${s.notices.length ? `<ul class="notices">${s.notices.map(notice).join("")}</ul>` : ""}
  </div>
  <div class="minimap" data-minimap hidden aria-label="Minimap"><canvas></canvas><div class="mm-me">${PLAYER_SVG}</div>${ROSE}</div>
  ${s.effects.length ? `<ul class="effects">${s.effects.map(effect).join("")}</ul>` : ""}
  ${sneak}
  ${s.banner ? banner(s.banner) : ""}
  ${s.prompt ? prompt(s.prompt) : ""}
</div>`;
}

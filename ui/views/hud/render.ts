// Our HUD (1.2 §d), render only. Souls-style bars whose drawn length grows with the stat's maximum, the sneak eye,
// the effect stack, the vastei plaque, the place banner, the prompt with the glyph of the device in use, and the
// notice stack, and the square minimap top right, north up (1.12 §5; drawn by minimap.ts). No compass bar and no
// quest marker, ever. No button: a tap on the stream never reaches the unfocused HUD view (the V5 touch run,
// docs/research/2026-11-01/1.12.md), so the phone's pad overlay's Start opens the windows; hud.menu stays for a later HUD.
import type { Bar, Effect, HudState, InputGlyph, Notice, PlaceBanner, Prompt } from "../../schema/generated/messages.ts";
import { esc } from "../core/html.ts";
import { ME } from "./me.ts";

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

// The bars' motion (owner look 1: the 5 Hz pushes redrew each bar, so it stepped, and the regeneration glint
// restarted at every push, so it flashed). Like Skyrim's own meter, the fill glides to each pushed value over the gap
// between pushes, and on a loss a pale trail holds where the bar was, then slides down after it; a rise carries the
// trail with it. CSS transitions on elements that persist (main.ts): the overlay view is unfocused and its JS timers
// are throttled to about one a second (hud-look 20261101T142258: the fill moved in 1.25 s plateaus under a 16 ms
// timer), while transitions run on the compositor. Pure: the transition each part takes for a push.
export const FILL_GLIDE = "width 0.24s linear";                                  // just over the 0.2 s between pushes
export const TRAIL_FOLLOW = "width 0.7s cubic-bezier(0.45, 0, 0.6, 1) 0.55s";  // held 0.55 s after the last loss
export function motion(was: number | undefined, now: number): { fill: string; trail: string } {
  return { fill: FILL_GLIDE, trail: was !== undefined && now < was ? TRAIL_FOLLOW : FILL_GLIDE };
}
export interface Meter { fill: number; trail: number }
export const meter = (pct: number): Meter => ({ fill: pct, trail: pct });

// The three standing bars are known by colour and place, as in Dark Souls; breath and grip come and go, so they
// carry their name. Rendered once at the pushed value; main.ts moves the widths in place from then on.
const NAMED = new Set<Bar["kind"]>(["breath", "climb"]);
const bar = (b: Bar, m?: Meter): string => {
  const f = m?.fill ?? fillPct(b), t = Math.max(f, m?.trail ?? f);
  const cls = [b.kind, b.kind === "health" && isLow([b]) ? "low" : ""].filter(Boolean).join(" ");
  return `<div class="row ${b.kind}" data-kind="${b.kind}"><div class="bar ${cls}" style="width:${barLength(b).toFixed(2)}rem"
  role="meter" aria-label="${BAR_NAME[b.kind]}" aria-valuenow="${Math.round(b.current)}" aria-valuemax="${Math.round(b.max)}">
  <div class="trail" style="width:${t.toFixed(1)}%"></div><div class="fill" style="width:${f.toFixed(1)}%"></div></div>${NAMED.has(b.kind) ? `<span class="bar-name">${BAR_NAME[b.kind]}</span>` : ""}</div>`;
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

export function renderBars(bars: Bar[], meters: Partial<Record<Bar["kind"], Meter>> = {}): string {
  return bars.filter((b) => b.shown).map((b) => bar(b, meters[b.kind])).join("");
}

// Vastei's shimmer (owner look 1: no "+N"): a light that runs across the plate once, its strength growing with the
// gain against what was carried before, so a few vastei on a big purse glint faintly and a haul flares. 0..1.
export function shimmer(gained: number | undefined, carried: number): number {
  if (gained === undefined || gained <= 0) return 0;
  const before = Math.max(0, carried - gained);
  const share = gained / Math.max(before + gained, 1);          // the share of the purse just won
  const size = Math.log10(1 + gained) / 3;                      // and its size: 1000 vastei is the full flare
  return Math.round(Math.min(1, Math.max(0.15, 0.5 * share + 0.5 * size)) * 100) / 100;
}

// The vastei mark: our own drawing, a scale-plate lozenge with a centre line.
const VMARK = `<svg class="vmark" viewBox="-8 -10 16 20" aria-hidden="true"><path d="M0 -9 L7 0 L0 9 L-7 0Z"/><path d="M0 -5 L0 5"/></svg>`;

export function render(s: HudState, meters: Partial<Record<Bar["kind"], Meter>> = {}): string {
  if (!s.visible) return `<div class="hud hidden"></div>`;
  const sneak = s.sneak.sneaking
    ? `<div class="sneak" data-eye="${s.sneak.eye}">${eye(s.sneak.eye)}<span class="sneak-word">${sneakWord(s.sneak.eye)}</span></div>` : "";
  const glow = shimmer(s.vastei.gained, s.vastei.carried);
  return `<div class="hud${isLow(s.bars) ? " low" : ""}">
  <div class="vignette" aria-hidden="true"></div>
  <div class="corner">
    ${s.notices.length ? `<ul class="notices">${s.notices.map(notice).join("")}</ul>` : ""}
    <div class="bars" data-bars>${renderBars(s.bars, meters)}</div>
    <div class="vastei${glow ? " up" : ""}"${glow ? ` data-glow="${glow}" style="--glow:${glow}"` : ""}>${VMARK}<span class="count">${s.vastei.carried}</span><span class="vlabel">Vastei</span></div>
  </div>
  <div class="minimap" data-minimap hidden aria-label="Minimap"><canvas></canvas><div class="mm-me">${ME}</div><span class="mm-n">N</span></div>
  ${s.effects.length ? `<ul class="effects">${s.effects.map(effect).join("")}</ul>` : ""}
  ${sneak}
  ${s.banner ? banner(s.banner) : ""}
  ${s.prompt ? prompt(s.prompt) : ""}
</div>`;
}

// One focus model for keyboard, pad and touch (0017 goal 2: every control reachable by pad and finger).
//
// - Keyboard: arrows move focus spatially, Enter/Space press (the platform's own button behaviour), Escape is back,
//   Tab is back too (the vanilla menus close on it), PageUp/PageDown and Q/E are the view's previous/next, +/- zoom.
// - Pad: the Gamepad API where the web view has it (d-pad and left stick move, A press, B back, LB/RB previous/next,
//   triggers zoom, right stick pans). In game, PrismaUI (Ultralight has no Gamepad API) dispatches
//   gamepadbuttondown on window.prismaUi.controls with the same W3C button index; the d-pad and buttons map alike.
// - Touch: every control is a button at least one text line tall; lists scroll natively.
// Nothing here is game state: only which control has focus.
export type NavAction =
  | "up" | "down" | "left" | "right" | "accept" | "back" | "prev" | "next" | "zoomIn" | "zoomOut"
  | "panUp" | "panDown" | "panLeft" | "panRight";

export interface NavHooks {
  action(a: NavAction): boolean;
  device(d: "keyboard" | "gamepad" | "touch"): void;
}

const FOCUSABLE = "button:not([disabled]),[data-nav]";
const DIRS: Partial<Record<NavAction, [number, number]>> = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };

const KEYS: Record<string, NavAction> = {
  ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", Escape: "back", Tab: "back",
  PageUp: "prev", PageDown: "next", q: "prev", e: "next", "+": "zoomIn", "=": "zoomIn", "-": "zoomOut",
  w: "panUp", s: "panDown", a: "panLeft", d: "panRight",
};

function visible(el: HTMLElement): boolean {
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== "hidden";
}

// The nearest focusable in a direction: centre in the half-plane, scored by distance along it plus twice the
// sideways offset, so a list walks in order and a column jump lands on the nearest row.
export function nearest(from: DOMRect, cands: { r: DOMRect }[], dx: number, dy: number): number {
  const cx = from.left + from.width / 2, cy = from.top + from.height / 2;
  let best = -1, score = Infinity;
  cands.forEach(({ r }, i) => {
    const x = r.left + r.width / 2 - cx, y = r.top + r.height / 2 - cy;
    const along = x * dx + y * dy, side = Math.abs(x * dy) + Math.abs(y * dx);
    if (along <= 1) return;
    const s = along + 2 * side;
    if (s < score) { score = s; best = i; }
  });
  return best;
}

export function installNav(h: NavHooks) {
  let lastKey: string | null = null;

  const move = (dx: number, dy: number): void => {
    const all = [...document.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(visible);
    if (!all.length) return;
    const cur = document.activeElement as HTMLElement | null;
    if (!cur || !all.includes(cur)) { focus(all[0]); return; }
    // Within a scrolling list, walk the list's order, so a long topic list moves one row at a time.
    const list = cur.closest<HTMLElement>("[data-list]");
    if (list && dy !== 0) {
      const items = [...list.querySelectorAll<HTMLElement>(FOCUSABLE)];
      const i = items.indexOf(cur) + dy;
      if (i >= 0 && i < items.length) { focus(items[i]); return; }
    }
    const others = all.filter((e) => e !== cur).map((el) => ({ el, r: el.getBoundingClientRect() }));
    const i = nearest(cur.getBoundingClientRect(), others, dx, dy);
    if (i >= 0) focus(others[i].el);
  };

  const focus = (el: HTMLElement): void => {
    el.focus({ preventScroll: true });
    el.scrollIntoView({ block: "nearest", inline: "nearest" });
    lastKey = el.dataset.key ?? null;
  };

  const input = (a: NavAction): void => {
    if (h.action(a)) return;
    const d = DIRS[a];
    if (d) { move(d[0], d[1]); return; }
    if (a === "accept") (document.activeElement as HTMLElement | null)?.click();
  };

  document.addEventListener("keydown", (e) => {
    h.device("keyboard");
    const a = KEYS[e.key];
    if (!a) return;
    // Enter and Space stay the platform's; arrows inside a text field would too, but our views have none.
    e.preventDefault();
    input(a);
  });
  document.addEventListener("pointerdown", (e) => { h.device(e.pointerType === "touch" ? "touch" : "keyboard"); });
  document.addEventListener("focusin", (e) => { lastKey = (e.target as HTMLElement).dataset?.key ?? lastKey; });

  // The pad, where the web view has the Gamepad API: read once per animation frame while a pad is connected.
  const held = new Map<string, number>();
  const REPEAT_MS = 180, FIRST_MS = 380;
  const pad = (t: number): void => {
    const p = [...(navigator.getGamepads?.() ?? [])].find((g) => g);
    if (!p) { padLoop = 0; return; }
    const b = (i: number) => !!p.buttons[i]?.pressed;
    const ax = p.axes[0] ?? 0, ay = p.axes[1] ?? 0, rx = p.axes[2] ?? 0, ry = p.axes[3] ?? 0;
    const want: [string, boolean, NavAction][] = [
      ["up", b(12) || ay < -0.6, "up"], ["down", b(13) || ay > 0.6, "down"],
      ["left", b(14) || ax < -0.6, "left"], ["right", b(15) || ax > 0.6, "right"],
      ["a", b(0), "accept"], ["b", b(1), "back"], ["lb", b(4), "prev"], ["rb", b(5), "next"],
      ["lt", b(6), "zoomOut"], ["rt", b(7), "zoomIn"],
      ["pu", ry < -0.5, "panUp"], ["pd", ry > 0.5, "panDown"], ["pl", rx < -0.5, "panLeft"], ["pr", rx > 0.5, "panRight"],
    ];
    for (const [k, on, a] of want) {
      if (!on) { held.delete(k); continue; }
      const since = held.get(k);
      if (since === undefined) { held.set(k, t + FIRST_MS); h.device("gamepad"); input(a); }
      else if (t >= since && !["a", "b", "lb", "rb"].includes(k)) { held.set(k, t + REPEAT_MS); input(a); }
    }
    padLoop = requestAnimationFrame(pad);
  };
  let padLoop = 0;
  window.addEventListener("gamepadconnected", () => { if (!padLoop) padLoop = requestAnimationFrame(pad); });
  const PRISMA_BUTTONS: Record<number, NavAction> = {
    12: "up", 13: "down", 14: "left", 15: "right", 0: "accept", 1: "back", 4: "prev", 5: "next", 6: "zoomOut", 7: "zoomIn",
  };
  const controls = (window as { prismaUi?: { controls?: EventTarget } }).prismaUi?.controls;
  controls?.addEventListener("gamepadbuttondown", (e) => {
    const a = PRISMA_BUTTONS[(e as CustomEvent<{ w3cButtonIndex: number }>).detail?.w3cButtonIndex];
    if (a) { h.device("gamepad"); input(a); }
  });

  return {
    input,
    // After a re-render, put focus back on the control with the same data-key, so a push never loses the pad's place.
    restore(): void {
      if (lastKey === null) return;
      const el = document.querySelector<HTMLElement>(`[data-key="${CSS.escape(lastKey)}"]`);
      if (el && document.activeElement !== el) el.focus({ preventScroll: true });
    },
  };
}

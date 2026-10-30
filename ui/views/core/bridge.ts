// The one seam between a view and ArgoniaCore (decision 0017 §3), browser side.
//
// In: ArgoniaCore calls window.argoniaPush(text) with one envelope (PrismaUI's InteropCall, which finds a global
// function by name, so the entry is a top-level alias of window.argonia.push). The text is decoded with the
// schema's validator; a refusal is logged and the view keeps what it showed.
// Out: an intent is checked with encodeIntent before it leaves and handed to window.argoniaIntent(text), the JS
// listener the SKSE side registers (PrismaUI RegisterJSListener). Every sent intent is also kept on
// window.argoniaSent, which the L3 harness reads; it is the record of what left, never state the view reads back.
// If 1.2 §0 picks Scaleform instead, only this file and the views change; the schema and the rules do not.
import { decodePush, encodeIntent, type IntentMessage, type PushMessage } from "../../schema/generated/messages.ts";
import { type NavAction, installNav } from "./nav.ts";
import { installScale } from "./scale.ts";

export type Device = "keyboard" | "gamepad" | "touch";

interface ArgoniaGlobal {
  push(text: string): boolean;
  input(action: NavAction): void;
  device(d: Device): void;
  errors: string[];
}
declare global {
  interface Window {
    argonia: ArgoniaGlobal;
    argoniaIntent?: (text: string) => void;
    argoniaPush: (text: string) => boolean;
    argoniaSent: string[];
  }
}

export interface ViewHooks {
  accepts: readonly string[];                 // the push types this view renders
  render(m: PushMessage): void;               // set the DOM from one decoded push
  action?(a: NavAction): boolean;             // a view's own use of an input (page turn, zoom); true if used
  back(): void;                               // Escape, the pad's B: close or Goodbye
  local?(el: HTMLElement): void;              // a click on a [data-ui] control: view-local presentation only
}

export function send(m: IntentMessage): boolean {
  const r = encodeIntent(m);
  if (!r.ok) { window.argonia.errors.push(`intent refused: ${r.error}`); console.error(r.error); return false; }
  window.argoniaSent.push(r.value);
  window.argoniaIntent?.(r.value);
  return true;
}

export function setDevice(d: Device): void {
  const b = document.body;
  if (b.dataset.device === d) return;
  b.dataset.device = d;
}

export function start(hooks: ViewHooks): void {
  window.argoniaSent = [];
  const errors: string[] = [];
  installScale();
  setDevice("keyboard");
  const nav = installNav({
    action: (a) => {
      if (a === "back") { hooks.back(); return true; }
      return hooks.action?.(a) ?? false;
    },
    device: setDevice,
  });
  window.argonia = {
    errors,
    push(text: string): boolean {
      const r = decodePush(text);
      if (!r.ok) { errors.push(r.error); console.error(r.error); return false; }
      if (!hooks.accepts.includes(r.value.type)) { errors.push(`${r.value.type}: not this view's`); return false; }
      hooks.render(r.value);
      nav.restore();
      return true;
    },
    input: (a) => nav.input(a),
    device: setDevice,
  };
  window.argoniaPush = (text: string) => window.argonia.push(text);
  document.addEventListener("click", (e) => {
    const el = (e.target as HTMLElement).closest<HTMLElement>("[data-intent],[data-ui]");
    if (!el || (el as HTMLButtonElement).disabled) return;
    if (el.dataset.ui !== undefined) { hooks.local?.(el); return; }
    send(JSON.parse(el.dataset.intent!) as IntentMessage);
  });
}

// Our wait window in the browser: one innerHTML per wait.state, re-drawn as the hours change here (presentation only:
// the hours leave in wait.pick). − and + (click, the pad's A), the arrows left and right and the slider set the hours;
// Escape, Tab, the pad's B and touch's B close.
import type { WaitState } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { clamp, close, render } from "./render.ts";

const root = document.getElementById("view")!;
let state: WaitState | undefined;
let hours = 1;

function draw(focus?: string): void {
  if (!state) return;
  hours = clamp(hours, state.max);
  root.innerHTML = render(state, hours);
  if (focus) root.querySelector<HTMLElement>(`[data-key="${focus}"]`)?.focus();
}

start({
  accepts: ["wait.state"],
  render(m) {
    if (m.type !== "wait.state") return;
    state = m.body;
    hours = m.body.hours;
    draw();
  },
  action(a) {
    if (!state || (a !== "left" && a !== "right")) return false;
    hours += a === "left" ? -1 : 1;
    draw((document.activeElement as HTMLElement | null)?.dataset.key ?? "go");
    return true;
  },
  local(el) {
    const was = el.dataset.key;
    if (el.dataset.ui === "less") hours -= 1;
    else if (el.dataset.ui === "more") hours += 1;
    else if (el.dataset.ui === "slide") hours = Number((el as HTMLInputElement).value);
    draw(was);
  },
  back() { send(close()); },
});
root.addEventListener("input", (e) => {
  const el = e.target as HTMLInputElement;
  if (el.dataset.ui === "slide") { hours = Number(el.value); draw(); }
});

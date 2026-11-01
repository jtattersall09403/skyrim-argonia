// Our wait window (1.12, lane 1.12-menus), render only: T and the pad's Select open it in place of Dear Diary's
// Sleep/Wait Menu. The time now, the hours (the stepper's − and +, the arrows left and right), and Wait (or Sleep,
// in a bed). ArgoniaCore runs the engine's own wait with the hours picked; the view only draws and sends wait.pick.
import type { WaitState } from "../../schema/generated/messages.ts";
import { esc, intentButton } from "../core/html.ts";

export const pick = (hours: number) => ({ type: "wait.pick" as const, v: 1 as const, body: { hours } });
export const close = () => ({ type: "view.close" as const, v: 1 as const, body: { view: "wait" as const } });

export const clamp = (h: number, max: number) => Math.min(Math.max(1, Math.round(h)), max);

export function render(s: WaitState, hours = s.hours): string {
  const h = clamp(hours, s.max);
  const verb = s.mode === "sleep" ? "Sleep" : "Wait";
  const unit = h === 1 ? "hour" : "hours";
  return `<section class="window wait" aria-label="${verb}">
  <header class="bar"><h1>${verb}</h1>${intentButton(close(), "close", "Close", `data-key="close"`)}</header>
  <p class="now">${esc(s.now)}</p>
  <div class="hours" role="group" aria-label="Hours">
    <button type="button" class="step" data-ui="less" data-key="less" aria-label="One hour less"${h <= 1 ? " disabled" : ""}>−</button>
    <span class="count" aria-live="polite"><span class="n">${h}</span> ${unit}</span>
    <button type="button" class="step" data-ui="more" data-key="more" aria-label="One hour more"${h >= s.max ? " disabled" : ""}>+</button>
  </div>
  <input class="slider" type="range" min="1" max="${s.max}" value="${h}" data-ui="slide" aria-label="Hours" tabindex="-1">
  ${intentButton(pick(h), "go", `${verb} ${h} ${unit}`, `data-key="go"`)}
</section>`;
}

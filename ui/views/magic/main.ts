// Our magic pane in the browser: one innerHTML per magic.state. A spell's name (click, Enter, the pad's A) readies it
// in the right hand, its "L" in the left; a power readies in the voice slot. Escape, Tab, the pad's B and touch's B
// close. The list walks in order (nav.ts's data-list); the arrows left and right move between a name and its "L".
import { send, start } from "../core/bridge.ts";
import { close, render } from "./render.ts";

const root = document.getElementById("view")!;

start({
  accepts: ["magic.state"],
  render(m) {
    if (m.type !== "magic.state") return;
    const well = root.querySelector<HTMLElement>(".well");
    const top = well?.scrollTop ?? 0;  // a re-push after an equip keeps the list where it was
    root.innerHTML = render(m.body);
    const now = root.querySelector<HTMLElement>(".well");
    if (now) now.scrollTop = top;
  },
  back() { send(close()); },
});

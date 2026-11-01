// Our System pane in the browser: one innerHTML per system.state. An entry (click, Enter, the pad's A) sends
// system.pick; Escape, Tab, the pad's B and touch's B close.
import { send, start } from "../core/bridge.ts";
import { close, render } from "./render.ts";

const root = document.getElementById("view")!;

start({
  accepts: ["system.state"],
  render(m) {
    if (m.type !== "system.state") return;
    root.innerHTML = render(m.body);
  },
  back() { send(close()); },
});

// The level sitting in the browser: one innerHTML per sitting.state; Escape and the pad's B rise.
import { send, start } from "../core/bridge.ts";
import { done, render } from "./render.ts";

const root = document.getElementById("view")!;

start({
  accepts: ["sitting.state"],
  render(m) {
    if (m.type !== "sitting.state") return;
    root.innerHTML = render(m.body);
  },
  back() { send(done()); },
});

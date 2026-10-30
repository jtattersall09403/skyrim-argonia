// The HUD in the browser: hud.state redraws the whole; hud.bars, the frequent update, redraws the bars alone.
import { start } from "../core/bridge.ts";
import { render, renderBars } from "./render.ts";

const root = document.getElementById("view")!;

start({
  accepts: ["hud.state", "hud.bars"],
  render(m) {
    if (m.type === "hud.state") { root.innerHTML = render(m.body); return; }
    if (m.type === "hud.bars") {
      const el = root.querySelector<HTMLElement>("[data-bars]");
      if (el) el.innerHTML = renderBars(m.body.bars);   // before any hud.state there is no HUD to update
    }
  },
  back() { /* the HUD takes no input; Escape belongs to the game */ },
});

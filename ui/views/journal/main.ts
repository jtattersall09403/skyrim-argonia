// The journal in the browser: one innerHTML per journal.state; Q/E, PageUp/PageDown and the pad's shoulders turn.
import type { JournalState } from "../../schema/generated/messages.ts";
import { send, start } from "../core/bridge.ts";
import { render, turn } from "./render.ts";

const root = document.getElementById("view")!;
let state: JournalState | null = null;

start({
  accepts: ["journal.state"],
  render(m) {
    if (m.type !== "journal.state") return;
    state = m.body;
    root.innerHTML = render(state);
  },
  action(a) {
    if (!state || (a !== "prev" && a !== "next")) return false;
    const m = turn(state, a === "prev" ? -1 : 1);
    if (m) send(m);
    return true;
  },
  back() { send({ type: "view.close", v: 1, body: { view: "journal" } }); },
});

// Intents any of our views sends.
import { ViewId } from "./common.ts";
import { intent, oneOf } from "./types.ts";

export const viewClose = intent("view.close", 1, "The player closed a view (Escape, the pad's B, the close button)", {
  view: oneOf(ViewId),
});

export const messages = [viewClose];

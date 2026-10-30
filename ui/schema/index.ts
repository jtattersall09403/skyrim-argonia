// The one source of the messages between ArgoniaCore and the views (1.1 §c). tools/schema_gen reads `messages`.
import * as chart from "./chart.ts";
import * as dialogue from "./dialogue.ts";
import * as hud from "./hud.ts";
import * as journal from "./journal.ts";
import * as sitting from "./sitting.ts";
import type { MessageDef } from "./types.ts";
import * as view from "./view.ts";

export const messages: readonly MessageDef[] = [
  ...dialogue.messages, ...journal.messages, ...hud.messages, ...chart.messages, ...sitting.messages, ...view.messages,
];

// The studio start's AWS calls as EC2 dry runs, with the switch's own restricted AWS user (secrets.env), through the
// Worker's own signing: describes the build machine and says whether the tag and the start would succeed. Changes
// nothing (DryRun), so it is safe while the machine is up.
//   node infra/cloudflare/test/studio_live.mjs
import fs from "node:fs"
import os from "node:os"
import { studioDryRun } from "../play-switch.js"
const env = Object.fromEntries([...fs.readFileSync(os.homedir() + "/.argonia/secrets.env", "utf8").matchAll(/^\s*([A-Z_]+)=(.*)$/gm)].map((m) => [m[1], m[2].trim()]))
const out = await studioDryRun({ AWS_KEY_ID: env.AWS_SWITCH_KEY_ID, AWS_SECRET: env.AWS_SWITCH_SECRET })
console.log(JSON.stringify(out))
process.exit(out.tag === "would succeed" && out.start === "would succeed" ? 0 : 1)

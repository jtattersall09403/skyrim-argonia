// The play switch end to end with its own restricted AWS user (secrets.env): start through the Worker's
// start path, time until the tunnel is healthy, then stop through its stop path.
//   ARGONIA_SWITCH_E2E=1 node infra/cloudflare/test/switch.mjs
// It really starts and then STOPS argonia-play, so it refuses unless armed: unarmed, it ran mid-checks on
// 2026-10-31 and stopped game-21's machine at 10:10:26. No runner (make check, npm test) sets the variable.
import fs from "node:fs"
import os from "node:os"
import worker from "../play-switch.js"
const env = Object.fromEntries([...fs.readFileSync(os.homedir() + "/.argonia/secrets.env", "utf8").matchAll(/^\s*([A-Z_]+)=(.*)$/gm)].map((m) => [m[1], m[2].trim()]))
const wenv = { AWS_KEY_ID: env.AWS_SWITCH_KEY_ID, AWS_SECRET: env.AWS_SWITCH_SECRET }
const cf = async (p) => (await (await fetch("https://api.cloudflare.com/client/v4" + p, { headers: { Authorization: "Bearer " + env.CLOUDFLARE_API_TOKEN } })).json()).result
const acct = env.CLOUDFLARE_ACCOUNT_ID
const [tun] = await cf(`/accounts/${acct}/cfd_tunnel?name=argonia-play&is_deleted=false`)
const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const status = async () => JSON.parse(await (await worker.fetch(new Request("https://x/argonia/status"), wenv)).text())
{ const s = await status()
  console.log(`will start then stop ${s.id} (${s.state}) via the play switch`)
  if (process.env.ARGONIA_SWITCH_E2E !== "1") { console.log("not armed: set ARGONIA_SWITCH_E2E=1 to run (it stops the machine)"); process.exit(0) } }
for (let s = await status(); s.state === "stopping"; s = await status()) await wait(3000)
const t0 = Date.now(); const secs = () => ((Date.now() - t0) / 1000).toFixed(0) + " s"
const r = await worker.fetch(new Request("https://x/argonia/start"), wenv)
console.log("start page:", r.status, (await r.text()).match(/<h1>(.*?)<\/h1>/)[1])
let running = false
for (let i = 0; i < 90; i++) {
  const s = await status(); if (s.state === "running" && !running) { running = true; console.log("EC2 running at", secs()) }
  const t = await cf(`/accounts/${acct}/cfd_tunnel/${tun.id}`)
  if (t.status === "healthy") { console.log("tunnel healthy (the stream page would load) at", secs()); break }
  await wait(2000)
}
const stop = await worker.fetch(new Request("https://x/argonia/stop"), wenv)
console.log("stop page:", stop.status, (await stop.text()).match(/<h1>(.*?)<\/h1>/)[1])
await wait(5000); console.log("after stop:", (await status()).state)

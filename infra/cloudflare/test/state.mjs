// Read-only check of the play switch's EC2 signing and parsing, with this machine's role credentials:
//   eval "$(aws configure export-credentials --format env)" && node infra/cloudflare/test/state.mjs
import worker from "../play-switch.js"
const env = { AWS_KEY_ID: process.env.AWS_ACCESS_KEY_ID, AWS_SECRET: process.env.AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN: process.env.AWS_SESSION_TOKEN }
const res = await worker.fetch(new Request("https://play.example/argonia/status"), env)
console.log(res.status, await res.text())

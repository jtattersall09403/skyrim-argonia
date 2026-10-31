// The play page's spot message (1.8 §2), without AWS:   node infra/cloudflare/test/spot.mjs
import assert from "node:assert/strict"
import { parseInstance, reclaimed, spotStatus, RECLAIMED_TEXT } from "../play-switch.js"
const inst = (state, spot) => `<reservationSet><item><instancesSet><item><instanceId>i-0abc123</instanceId><instanceState><code>80</code><name>${state}</name></instanceState>${spot ? `<spotInstanceRequestId>${spot}</spotInstanceRequestId>` : ""}<launchTime>2026-10-31T10:00:00.000Z</launchTime></item></instancesSet></item></reservationSet>`
assert.deepEqual(parseInstance(inst("stopped", "sir-abc12345")), { id: "i-0abc123", state: "stopped", launched: "2026-10-31T10:00:00.000Z", ip: null, spot: "sir-abc12345" })
assert.equal(parseInstance(inst("running")).spot, null, "an on-demand machine has no spot request")
const req = (code) => `<spotInstanceRequestSet><item><state>disabled</state><status><code>${code}</code><updateTime>x</updateTime><message>m</message></status></item></spotInstanceRequestSet>`
assert.equal(spotStatus(req("instance-stopped-no-capacity")), "instance-stopped-no-capacity")
assert.equal(spotStatus("<x/>"), null)
assert.equal(reclaimed("stopped", "instance-stopped-no-capacity"), true, "AWS stopped it: say so")
assert.equal(reclaimed("stopped", "instance-stopped-by-price"), true)
assert.equal(reclaimed("stopping", "marked-for-stop"), true, "the notice is out: say so while it stops")
assert.equal(reclaimed("running", "marked-for-stop"), true, "the two minutes before the stop")
assert.equal(reclaimed("stopped", "instance-stopped-by-user"), false, "the owner, idle-stop or a cap stopped it")
assert.equal(reclaimed("running", "fulfilled"), false)
assert.equal(reclaimed("stopped", null), false, "no read: no claim")
assert.match(RECLAIMED_TEXT, /^AWS took the machine back; your game was saved/)
console.log("spot message: 12 checks pass")

// The start retry (owner #29): a settling refusal retries for two minutes from the first, then shows the error.
import { startRetry, START_RETRY_MS } from "../play-switch.js"
const spotErr = "EC2 StartInstances 400: <Code>IncorrectSpotRequestState</Code>"
assert.equal(START_RETRY_MS, 120e3)
assert.equal(startRetry(spotErr, 0, 1e6), true, "the first refusal: starting…")
assert.equal(startRetry(spotErr, 1e6, 1e6 + 119e3), true, "within two minutes: keep trying")
assert.equal(startRetry(spotErr, 1e6, 1e6 + 121e3), false, "past two minutes: show the error")
assert.equal(startRetry("EC2 StartInstances 400: <Code>IncorrectInstanceState</Code>", 0, 1e6), true, "the instance still stopping")
assert.equal(startRetry("EC2 StartInstances 403: <Code>UnauthorizedOperation</Code>", 0, 1e6), false, "a real fault: no retry")
console.log("start retry: 5 checks pass")

// The start page through the Worker, with EC2 stubbed: a settling refusal shows "Starting…" and sets the cookie.
import worker from "../play-switch.js"
const env = { AWS_KEY_ID: "k", AWS_SECRET: "s" }
globalThis.fetch = async (u) => String(u).includes("StartInstances") ? new Response(spotErr, { status: 400 })
  : new Response(String(u).includes("DescribeInstances") ? inst("stopped") : "", { status: 200 })
let r = await worker.fetch(new Request("https://x/argonia/start"), env), body = await r.text()
assert.match(body, /<h1>Starting…<\/h1>/); assert.match(r.headers.get("set-cookie"), /argoniaStartRetry=\d+/)
r = await worker.fetch(new Request("https://x/argonia/start", { headers: { cookie: `argoniaStartRetry=${Date.now() - 130e3}` } }), env)
assert.match(await r.text(), /did not start/, "past the window: the error")
console.log("start page: 3 checks pass")

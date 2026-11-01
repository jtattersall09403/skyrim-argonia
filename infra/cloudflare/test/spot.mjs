// The play page's spot message (1.8 §2), without AWS:   node infra/cloudflare/test/spot.mjs
import assert from "node:assert/strict"
import { parseInstance, reclaimed, spotStatus, RECLAIMED_TEXT } from "../play-switch.js"
const inst = (state, spot) => `<reservationSet><item><instancesSet><item><instanceId>i-0abc123</instanceId><instanceState><code>80</code><name>${state}</name></instanceState>${spot ? `<spotInstanceRequestId>${spot}</spotInstanceRequestId>` : ""}<launchTime>2026-10-31T10:00:00.000Z</launchTime></item></instancesSet></item></reservationSet>`
assert.deepEqual(parseInstance(inst("stopped", "sir-abc12345")), { id: "i-0abc123", state: "stopped", launched: "2026-10-31T10:00:00.000Z", ip: null, spot: "sir-abc12345", build: null, buildUtc: null })
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

// The start page through the Worker, with EC2 stubbed: a settling refusal on every standby shows "Starting…" and
// sets the cookie; a refusal on the best one starts the next (the pool, 1.8 §7).
import worker from "../play-switch.js"
const POOL = JSON.stringify([{ name: "argonia-play", label: "paris", region: "eu-west-3", type: "g6.xlarge", az: "euw3-az2" },
                             { name: "argonia-play-ie", label: "ireland", region: "eu-west-1", type: "g5.xlarge", az: "euw1-az1" }])
const capErr = "EC2 StartInstances 500: <Code>InsufficientInstanceCapacity</Code>"
const stub = (refuse, score = {}) => async (u) => {
  u = String(u)
  const region = /ec2\.([a-z0-9-]+)\./.exec(u)?.[1]
  if (u.includes("StartInstances")) return refuse(region) ? new Response(refuse(region), { status: 400 }) : new Response("<ok/>", { status: 200 })
  if (u.includes("GetSpotPlacementScores")) return new Response(`<x><item><availabilityZoneId>z</availabilityZoneId><score>${score[region] ?? 5}</score></item></x>`)
  return new Response(u.includes("DescribeInstances") ? inst("stopped") : "", { status: 200 })
}
const env = () => ({ AWS_KEY_ID: "k", AWS_SECRET: "s", POOL, DOMAIN: "x" })
globalThis.fetch = stub(() => spotErr)
let r = await worker.fetch(new Request("https://x/argonia/start"), env()), body = await r.text()
assert.match(body, /<h1>Starting…<\/h1>/); assert.match(r.headers.get("set-cookie"), /argoniaStartRetry=\d+/)
r = await worker.fetch(new Request("https://x/argonia/start", { headers: { cookie: `argoniaStartRetry=${Date.now() - 130e3}` } }), env())
assert.match(await r.text(), /No game machine could start/, "past the window: the error")
// Ireland scores better but has no capacity: Paris starts, and this browser is sent to Paris
globalThis.fetch = stub((region) => region === "eu-west-1" ? capErr : null, { "eu-west-1": 9, "eu-west-3": 3 })
r = await worker.fetch(new Request("https://x/"), env()); body = await r.text()
assert.match(body, /<h1>Starting Paris<\/h1>/); assert.match(r.headers.get("set-cookie"), /argoniaMachine=argonia-play;/)
// both have room: the better score (Ireland) starts
globalThis.fetch = stub(() => null, { "eu-west-1": 9, "eu-west-3": 3 })
r = await worker.fetch(new Request("https://x/"), env())
assert.match(await r.text(), /<h1>Starting Ireland<\/h1>/)
console.log("start page: 5 checks pass")

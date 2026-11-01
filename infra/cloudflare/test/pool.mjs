// The pool's choices (1.8 §7), without AWS:   node infra/cloudflare/test/pool.mjs
import assert from "node:assert/strict"
import { inUse, startOrder, placementScore, originHost, parseInstance } from "../play-switch.js"

const paris = { name: "argonia-play", label: "paris", state: "stopped", buildUtc: "2026-11-01T10:00:00Z" }
const ireland = { name: "argonia-play-ie", label: "ireland", state: "stopped", buildUtc: "2026-11-01T10:00:00Z" }

// the best score starts first; a refusal falls to the next (the order is the fallback)
assert.deepEqual(startOrder([paris, ireland], { "argonia-play": 3, "argonia-play-ie": 9 }).map((m) => m.label), ["ireland", "paris"])
assert.deepEqual(startOrder([paris, ireland], { "argonia-play": 9, "argonia-play-ie": 3 }).map((m) => m.label), ["paris", "ireland"])
// no scores (the permission missing): POOL's order
assert.deepEqual(startOrder([paris, ireland], {}).map((m) => m.label), ["paris", "ireland"])
// a machine a deploy has not reached is only a fallback, whatever its score
const old = { ...paris, buildUtc: "2026-10-31T10:00:00Z" }
assert.deepEqual(startOrder([old, ireland], { "argonia-play": 9, "argonia-play-ie": 2 }).map((m) => m.label), ["ireland", "paris"])
// the machine this browser just started stays first on a reload
assert.deepEqual(startOrder([paris, ireland], { "argonia-play": 9, "argonia-play-ie": 3 }, "argonia-play-ie").map((m) => m.label), ["ireland", "paris"])
// only stopped machines are started
assert.deepEqual(startOrder([{ ...paris, state: "stopping" }, ireland], {}).map((m) => m.label), ["ireland"])

// the machine in use: this browser's if up; else one no agent holds; else none (start one)
const up = (m) => ({ ...m, state: "running" })
assert.equal(inUse([up(paris), up(ireland)], "argonia-play-ie", new Set())?.label, "ireland")
assert.equal(inUse([up(paris), ireland], "argonia-play-ie", new Set())?.label, "paris")
assert.equal(inUse([up(paris), ireland], undefined, new Set(["argonia-play"])), null)
assert.equal(inUse([paris, ireland], undefined, new Set()), null)
// even an agent's machine is the owner's if this browser is already on it (never cut a stream)
assert.equal(inUse([up(paris)], "argonia-play", new Set(["argonia-play"]))?.label, "paris")

// AWS's answer: the machine's zone, else the region's best
const xml = `<GetSpotPlacementScoresResponse><spotPlacementScoreSet><item><region>eu-west-1</region><availabilityZoneId>euw1-az1</availabilityZoneId><score>4</score></item><item><region>eu-west-1</region><availabilityZoneId>euw1-az3</availabilityZoneId><score>9</score></item></spotPlacementScoreSet></GetSpotPlacementScoresResponse>`
assert.equal(placementScore(xml, "euw1-az1"), 4)
assert.equal(placementScore(xml, "euw1-az2"), 9)
assert.equal(placementScore("<x/>", "euw1-az1"), null)

assert.equal(originHost("play.jacktat-play.stream", "ireland", "jacktat-play.stream"), "play-ireland.jacktat-play.stream")
assert.equal(originHost("sunshine.jacktat-play.stream", "paris", "jacktat-play.stream"), "sunshine-paris.jacktat-play.stream")

const di = `<instancesSet><item><instanceId>i-0abc</instanceId><instanceState><code>80</code><name>stopped</name></instanceState><tagSet><item><key>argonia-build</key><value>ef7258d</value></item><item><key>argonia-build-utc</key><value>2026-11-01T10:40:00Z</value></item></tagSet></item></instancesSet>`
const s = parseInstance(di)
assert.equal(s.build, "ef7258d"); assert.equal(s.buildUtc, "2026-11-01T10:40:00Z"); assert.equal(s.state, "stopped")
console.log("pool: ok")

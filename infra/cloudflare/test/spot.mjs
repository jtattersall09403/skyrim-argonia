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

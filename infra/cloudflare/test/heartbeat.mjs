// The heartbeat stop rule, without AWS:   node infra/cloudflare/test/heartbeat.mjs
import assert from "node:assert/strict"
import { heartbeatStop } from "../play-switch.js"
const min = 60e3, launched = Date.parse("2026-10-29T15:00:00Z")
const at = (m) => launched + m * min, iso = (m) => new Date(at(m)).toISOString()
assert.equal(heartbeatStop(launched, at(10), null), false, "a boot is never cut short")
assert.equal(heartbeatStop(launched, at(29), iso(-60)), false, "a beat from before this start does not count yet")
assert.equal(heartbeatStop(launched, at(31), null), true, "no heartbeat 30 min after the start: stop")
assert.equal(heartbeatStop(launched, at(45), iso(10)), true, "a heartbeat 35 min old: stop")
assert.equal(heartbeatStop(launched, at(45), iso(40)), false, "a fresh heartbeat: leave it to idle-stop")
assert.equal(heartbeatStop(null, at(45), null), false, "no launch time: never stop on it")
console.log("heartbeat rule: 6 checks pass")

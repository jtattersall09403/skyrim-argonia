// The origin host and instance parsing, without AWS:   node infra/cloudflare/test/pool.mjs
import assert from "node:assert/strict"
import { originHost, parseInstance } from "../play-switch.js"

assert.equal(originHost("play.jacktat-play.stream", "ireland", "jacktat-play.stream"), "play-ireland.jacktat-play.stream")
assert.equal(originHost("sunshine.jacktat-play.stream", "paris", "jacktat-play.stream"), "sunshine-paris.jacktat-play.stream")

const di = `<instancesSet><item><instanceId>i-0abc</instanceId><instanceState><code>80</code><name>stopped</name></instanceState><tagSet><item><key>argonia-build</key><value>ef7258d</value></item><item><key>argonia-build-utc</key><value>2026-11-01T10:40:00Z</value></item></tagSet></item></instancesSet>`
const s = parseInstance(di)
assert.equal(s.build, "ef7258d"); assert.equal(s.buildUtc, "2026-11-01T10:40:00Z"); assert.equal(s.state, "stopped")
console.log("origin: ok")

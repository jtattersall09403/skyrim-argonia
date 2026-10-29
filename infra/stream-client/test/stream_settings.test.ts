import { test } from "node:test"
import assert from "node:assert/strict"
import { streamSize, bitrateFor, MAX_EDGE, MIN_KBPS, MAX_KBPS } from "../src/stream_settings.ts"

test("the stream matches the screen's physical pixels", () => {
    assert.deepEqual(streamSize(1280, 800, 2), { width: 2560, height: 1600 })   // MacBook Air at 2x
    assert.deepEqual(streamSize(1920, 1080, 1), { width: 1920, height: 1080 })  // a monitor
})

test("a large screen keeps its shape inside MAX_EDGE, with even sides", () => {
    const s = streamSize(1176, 1086, 2.5)   // Magic V5 unfolded, about 2940 x 2715 physical
    assert.ok(Math.max(s.width, s.height) <= MAX_EDGE)
    assert.equal(s.width % 2, 0); assert.equal(s.height % 2, 0)
    assert.ok(Math.abs(s.width / s.height - 1176 / 1086) < 0.01)
})

test("the folded phone in landscape stays wide", () => {
    const s = streamSize(915, 412, 2.625)
    assert.ok(s.width > s.height * 2)
})

test("bitrate follows pixels inside its bounds", () => {
    assert.equal(bitrateFor(640, 360), MIN_KBPS)
    assert.equal(bitrateFor(3840, 2160), MAX_KBPS)
    const mid = bitrateFor(1920, 1080)
    assert.ok(mid > MIN_KBPS && mid < MAX_KBPS)
})

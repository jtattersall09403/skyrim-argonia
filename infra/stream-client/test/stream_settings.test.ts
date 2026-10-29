import { test } from "node:test"
import assert from "node:assert/strict"
import { streamSize, bitrateFor, fullScreenCss, MAX_EDGE, MAX_HEIGHT, MIN_KBPS, MAX_KBPS } from "../src/stream_settings.ts"

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

test("a tall screen stays within MAX_HEIGHT", () => {
    const s = streamSize(784, 724, 3)   // Magic V5 unfolded in landscape, full screen: 2352 x 2172 physical
    assert.ok(s.height <= MAX_HEIGHT)
    assert.ok(Math.abs(s.width / s.height - 784 / 724) < 0.01)
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

test("the stream is sized to the whole screen in its current orientation", () => {
    // Magic V5 unfolded in landscape: the page was 784 x 667 before full screen, the screen 784 x 724
    assert.deepEqual(fullScreenCss({ width: 784, height: 724 }, true), { width: 784, height: 724 })
    // a browser that keeps portrait screen sizes while the device is landscape
    assert.deepEqual(fullScreenCss({ width: 724, height: 784 }, true), { width: 784, height: 724 })
    assert.deepEqual(fullScreenCss({ width: 784, height: 724 }, false), { width: 724, height: 784 })
})

import { test } from "node:test"
import assert from "node:assert/strict"
import { MarkerDetector, PressPairer, patchTone, phaseOf, samplePoints, type MarkerPhase } from "../src/marker_detect.ts"

/** A synthetic RGBA patch: flat grey level plus optional per-pixel noise (codec ringing). */
function patch(level: number, noise = 0, n = 16, seed = 1): Uint8ClampedArray {
    const out = new Uint8ClampedArray(n * 4)
    let s = seed
    for (let i = 0; i < n; i++) {
        s = (s * 1103515245 + 12345) & 0x7fffffff
        const v = level + (noise ? ((s % (2 * noise + 1)) - noise) : 0)
        out.set([v, v, v, 255], i * 4)
    }
    return out
}
/** Game-like content: a gradient of colours. */
function busy(n = 16): Uint8ClampedArray {
    const out = new Uint8ClampedArray(n * 4)
    for (let i = 0; i < n; i++) out.set([i * 15, 255 - i * 15, (i * 37) % 255, 255], i * 4)
    return out
}

test("tones: flat dark is black, flat light is white, noisy or mid grey is other", () => {
    assert.equal(patchTone(patch(10, 8)), "black")
    assert.equal(patchTone(patch(245, 8)), "white")
    assert.equal(patchTone(patch(128)), "other")
    assert.equal(patchTone(busy()), "other")
    assert.equal(patchTone(new Uint8ClampedArray(0)), "other")
})

test("phase needs both halves flat and opposite", () => {
    assert.equal(phaseOf("black", "white"), "BW")
    assert.equal(phaseOf("white", "black"), "WB")
    assert.equal(phaseOf("black", "black"), null) // a black desktop corner is not a marker
    assert.equal(phaseOf("white", "other"), null)
})

test("detector fires once per flash on synthetic frames, including back-to-back alternating flashes", () => {
    const frame = (l: Uint8ClampedArray, r: Uint8ClampedArray): MarkerPhase => phaseOf(patchTone(l), patchTone(r))
    const content = () => frame(busy(), busy())
    const bw = () => frame(patch(12, 6), patch(240, 6))
    const wb = () => frame(patch(240, 6), patch(12, 6))
    const black = () => frame(patch(5), patch(5))
    // content, flash BW 3 frames, content, flash WB 3 frames, then WB directly followed by BW, then a black screen
    const frames = [content, content, bw, bw, bw, content, wb, wb, wb, content, wb, wb, bw, bw, black, black, black]
    const d = new MarkerDetector()
    const fired = frames.map((f, i) => d.push(f()) ? i : -1).filter((i) => i >= 0)
    assert.deepEqual(fired, [2, 6, 10, 12])
    assert.equal(d.detections, 4)
})

test("sample points scale with the stream against the desktop", () => {
    assert.deepEqual(samplePoints(1920, 1920, 24), { left: [12, 12], right: [36, 12], patch: 9 })
    const s = samplePoints(1280, 1920, 24)
    assert.equal(s.right[0], 24)
    assert.equal(s.patch, 6)
})

test("pairing takes the most recent input before the flash, drops those it passes, ignores stale ones", () => {
    const p = new PressPairer(1000)
    p.input({ at: 100, source: "touch", what: "a" })
    p.input({ at: 120, source: "touch", what: "b" })
    const a = p.detect(180)!
    assert.equal(a.input.what, "b")
    assert.equal(a.ms, 60)
    assert.equal(a.pending, 2)
    assert.equal(p.detect(200), null) // nothing left
    p.input({ at: 1000, source: "keyboard", what: "KeyE" })
    assert.equal(p.detect(2500), null) // older than the window
    p.input({ at: 3000, source: "gamepad", what: "a" })
    assert.equal(p.detect(3000.5), null) // a flash cannot precede its press by under a millisecond
    assert.equal(p.detect(3075)!.ms, 75)
})

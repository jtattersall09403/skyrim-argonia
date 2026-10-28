// Press-to-screen marker detection (chunk 0.0 §c). The host's marker (marker/marker.cs) flashes, on every new
// press, a two-tone square in the desktop's top-left corner: left half black and right half white, or the
// reverse, alternating per press, shown for about three frames. A two-tone split at that exact place almost
// never occurs in game or desktop content, so a frame counts as a marker only when both halves are flat and
// of opposite tones; a detection is the first frame of a marker phase that differs from the previous frame's.

export type Tone = "black" | "white" | "other"
export type MarkerPhase = "BW" | "WB" | null

/** Thresholds on 0..255 luma: a flat patch (stddev under FLAT) darker than BLACK or lighter than WHITE. */
export const BLACK = 70
export const WHITE = 185
export const FLAT = 28

/** The tone of an RGBA patch (ImageData.data layout). */
export function patchTone(rgba: ArrayLike<number>): Tone {
    const n = Math.floor(rgba.length / 4)
    if (n === 0) return "other"
    let sum = 0
    let sumSq = 0
    for (let i = 0; i < n; i++) {
        const y = 0.2126 * rgba[i * 4] + 0.7152 * rgba[i * 4 + 1] + 0.0722 * rgba[i * 4 + 2]
        sum += y
        sumSq += y * y
    }
    const mean = sum / n
    const sd = Math.sqrt(Math.max(0, sumSq / n - mean * mean))
    if (sd > FLAT) return "other"
    if (mean < BLACK) return "black"
    if (mean > WHITE) return "white"
    return "other"
}

export function phaseOf(left: Tone, right: Tone): MarkerPhase {
    if (left === "black" && right === "white") return "BW"
    if (left === "white" && right === "black") return "WB"
    return null
}

/** Feed one phase per decoded frame; returns true on the frame a new flash first shows. */
export class MarkerDetector {
    private last: MarkerPhase = null
    detections = 0
    frames = 0

    push(phase: MarkerPhase): boolean {
        this.frames++
        const fired = phase !== null && phase !== this.last
        this.last = phase
        if (fired) this.detections++
        return fired
    }
}

/** Where to sample in video pixels: the centres of the two marker halves, scaled from desktop to stream size. */
export function samplePoints(videoWidth: number, desktopWidth: number, markerHalfPx: number): { left: [number, number], right: [number, number], patch: number } {
    const scale = desktopWidth > 0 ? videoWidth / desktopWidth : 1
    const half = markerHalfPx * scale
    const patch = Math.max(2, Math.floor(half * 0.4))
    return { left: [half * 0.5, half * 0.5], right: [half * 1.5, half * 0.5], patch }
}

export type PendingInput = { at: number, source: string, what: string }
export type Pairing = { input: PendingInput, ms: number, pending: number }

/**
 * Pairs each detected flash with the most recent input sent before it (the brief's rule) that is not older than
 * `windowMs`; the inputs it passes over are dropped (they were merged into the same host flash or missed).
 */
export class PressPairer {
    private pending: PendingInput[] = []
    private windowMs: number
    private minMs: number
    constructor(windowMs = 1000, minMs = 1) { this.windowMs = windowMs; this.minMs = minMs }

    input(p: PendingInput) { this.pending.push(p) }

    detect(at: number): Pairing | null {
        this.pending = this.pending.filter((p) => at - p.at <= this.windowMs)
        let idx = -1
        for (let i = this.pending.length - 1; i >= 0; i--) {
            if (at - this.pending[i].at >= this.minMs) { idx = i; break }
        }
        if (idx < 0) return null
        const input = this.pending[idx]
        const pending = idx + 1
        this.pending = this.pending.slice(idx + 1)
        return { input, ms: Math.round((at - input.at) * 10) / 10, pending }
    }
}

import { test } from "node:test"
import assert from "node:assert/strict"
import { median, p95, quantile, summarize, summarizeFields } from "../src/stats_math.ts"
import { rtcRecord } from "../src/rtc_stats.ts"

test("median of odd and even counts, ignoring nulls and NaN", () => {
    assert.equal(median([3, 1, 2]), 2)
    assert.equal(median([4, 1, 3, 2]), 2.5)
    assert.equal(median([null, 5, undefined, NaN, 1]), 3)
    assert.equal(median([]), null)
})

test("p95 interpolates between closest ranks (numpy linear)", () => {
    const xs = Array.from({ length: 101 }, (_, i) => i) // 0..100
    assert.equal(p95(xs), 95)
    assert.equal(quantile([10, 20], 0.95), 19.5)
    assert.equal(p95([7]), 7)
})

test("summary rounds to 2 places and counts only finite values", () => {
    const s = summarize([1, 2, 3, 4, null, Infinity])
    assert.deepEqual(s, { n: 4, median: 2.5, p95: 3.85, min: 1, max: 4, mean: 2.5 })
})

test("summarizeFields over records", () => {
    const recs = [{ rttMs: 10, fps: 60 }, { rttMs: 30, fps: 59 }, { rttMs: 20, fps: null as number | null }]
    const s = summarizeFields(recs, ["rttMs", "fps"])
    assert.equal(s.rttMs.median, 20)
    assert.equal(s.fps.n, 2)
})

test("rtcRecord: round trip from the selected pair, per-second deltas", () => {
    const report = (bytes: number, frames: number, decode: number, lost: number, got: number, dropped: number) => [
        { id: "T1", type: "transport", selectedCandidatePairId: "CP1" },
        { id: "CP1", type: "candidate-pair", localCandidateId: "L1", remoteCandidateId: "R1", currentRoundTripTime: 0.0234, availableIncomingBitrate: 20_000_000 },
        { id: "CP2", type: "candidate-pair", localCandidateId: "L1", remoteCandidateId: "R1", currentRoundTripTime: 0.5 },
        { id: "L1", type: "local-candidate", candidateType: "srflx", protocol: "udp" },
        { id: "R1", type: "remote-candidate", candidateType: "host" },
        { id: "C1", type: "codec", mimeType: "video/H264" },
        { id: "V1", type: "inbound-rtp", kind: "video", codecId: "C1", jitter: 0.0031, bytesReceived: bytes, framesDecoded: frames, totalDecodeTime: decode,
          packetsLost: lost, packetsReceived: got, framesDropped: dropped, frameWidth: 1920, frameHeight: 1080, framesPerSecond: 60,
          jitterBufferDelay: frames * 0.02, jitterBufferEmittedCount: frames },
    ]
    const first = rtcRecord(report(1_000_000, 600, 3.0, 2, 10_000, 1), null, 10_000)
    assert.equal(first.record.rttMs, 23.4)
    assert.equal(first.record.bitrateKbps, null)
    const second = rtcRecord(report(2_250_000, 660, 3.3, 3, 10_999, 4), first.totals, 11_000)
    const r = second.record
    assert.equal(r.rttMs, 23.4)
    assert.equal(r.jitterMs, 3.1)
    assert.equal(r.bitrateKbps, 10_000) // 1.25 MB in 1 s
    assert.equal(r.decodeMs, 5) // 0.3 s over 60 frames
    assert.equal(r.framesDropped, 3)
    assert.equal(r.lossPct, 0.1) // 1 lost of 1000
    assert.equal(r.jitterBufferMs, 20)
    assert.equal(r.resolution, "1920x1080")
    assert.equal(r.codec, "H264")
    assert.deepEqual(r.candidate, { local: "srflx", remote: "host", protocol: "udp", relayProtocol: null })
    assert.equal(r.availableInKbps, 20_000)
})

test("rtcRecord: no video yet gives nulls, not a throw", () => {
    const { record, totals } = rtcRecord([], null, 0)
    assert.equal(record.rttMs, null)
    assert.equal(totals, null)
})

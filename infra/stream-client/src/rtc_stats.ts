// One per-second record from an RTCPeerConnection.getStats() report (chunk 0.0 §c). Pure: the report is passed
// as its values, the previous totals come back for the next call. Adds what upstream's stats.ts lacks: the round
// trip from the selected candidate pair, per-second deltas (bitrate, loss, drops) and the candidate types.

type Stat = Record<string, any>

export type RtcTotals = { at: number, bytes: number, framesDecoded: number, totalDecodeTime: number, framesDropped: number, packetsLost: number, packetsReceived: number, jbDelay: number, jbEmitted: number }

export type RtcRecord = {
    rttMs: number | null
    jitterMs: number | null
    jitterBufferMs: number | null
    lossPct: number | null
    packetsLost: number | null
    bitrateKbps: number | null
    fps: number | null
    decodeMs: number | null
    framesDropped: number | null
    framesDroppedTotal: number | null
    resolution: string | null
    codec: string | null
    candidate: { local: string | null, remote: string | null, protocol: string | null, relayProtocol: string | null } | null
    availableInKbps: number | null
}

const num = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null
const round = (v: number | null, d = 1) => v === null ? null : Math.round(v * 10 ** d) / 10 ** d

export function rtcRecord(stats: Iterable<Stat>, prev: RtcTotals | null, now: number): { record: RtcRecord, totals: RtcTotals | null } {
    const byId = new Map<string, Stat>()
    const all: Stat[] = []
    for (const s of stats) { all.push(s); if (s.id) byId.set(s.id, s) }
    const video = all.find((s) => s.type === "inbound-rtp" && (s.kind === "video" || s.mediaType === "video")) ?? null

    // the selected pair: transport.selectedCandidatePairId (Chrome), else a nominated succeeded pair (Firefox: selected)
    let pair: Stat | null = null
    const transport = all.find((s) => s.type === "transport" && s.selectedCandidatePairId)
    if (transport) pair = byId.get(transport.selectedCandidatePairId) ?? null
    if (!pair) pair = all.find((s) => s.type === "candidate-pair" && (s.selected || (s.nominated && s.state === "succeeded"))) ?? null
    const local = pair ? byId.get(pair.localCandidateId) ?? null : null
    const remote = pair ? byId.get(pair.remoteCandidateId) ?? null : null
    const codecStat = video?.codecId ? byId.get(video.codecId) : null

    const record: RtcRecord = {
        rttMs: round(num(pair?.currentRoundTripTime) === null ? null : pair!.currentRoundTripTime * 1000),
        jitterMs: round(num(video?.jitter) === null ? null : video!.jitter * 1000),
        jitterBufferMs: null,
        lossPct: null,
        packetsLost: null,
        bitrateKbps: null,
        fps: round(num(video?.framesPerSecond)),
        decodeMs: null,
        framesDropped: null,
        framesDroppedTotal: num(video?.framesDropped),
        resolution: video && num(video.frameWidth) ? `${video.frameWidth}x${video.frameHeight}` : null,
        codec: codecStat?.mimeType ? String(codecStat.mimeType).replace(/^video\//, "") : null,
        candidate: pair ? { local: local?.candidateType ?? null, remote: remote?.candidateType ?? null, protocol: local?.protocol ?? null, relayProtocol: local?.relayProtocol ?? null } : null,
        availableInKbps: null,
    }
    if (!video) return { record, totals: prev }

    const totals: RtcTotals = {
        at: now,
        bytes: num(video.bytesReceived) ?? 0,
        framesDecoded: num(video.framesDecoded) ?? 0,
        totalDecodeTime: num(video.totalDecodeTime) ?? 0,
        framesDropped: num(video.framesDropped) ?? 0,
        packetsLost: num(video.packetsLost) ?? 0,
        packetsReceived: num(video.packetsReceived) ?? 0,
        jbDelay: num(video.jitterBufferDelay) ?? 0,
        jbEmitted: num(video.jitterBufferEmittedCount) ?? 0,
    }
    if (prev && now > prev.at) {
        const dt = (now - prev.at) / 1000
        const frames = totals.framesDecoded - prev.framesDecoded
        record.bitrateKbps = round((totals.bytes - prev.bytes) * 8 / 1000 / dt, 0)
        if (record.fps === null) record.fps = round(frames / dt)
        record.decodeMs = frames > 0 ? round((totals.totalDecodeTime - prev.totalDecodeTime) / frames * 1000, 2) : null
        record.framesDropped = totals.framesDropped - prev.framesDropped
        const lost = totals.packetsLost - prev.packetsLost
        const got = totals.packetsReceived - prev.packetsReceived
        record.packetsLost = lost
        record.lossPct = lost + got > 0 ? round(Math.max(0, lost) / (Math.max(0, lost) + got) * 100, 2) : 0
        const emitted = totals.jbEmitted - prev.jbEmitted
        record.jitterBufferMs = emitted > 0 ? round((totals.jbDelay - prev.jbDelay) / emitted * 1000) : null
    }
    if (num(pair?.availableIncomingBitrate) !== null) record.availableInKbps = round(pair!.availableIncomingBitrate / 1000, 0)
    return { record, totals }
}

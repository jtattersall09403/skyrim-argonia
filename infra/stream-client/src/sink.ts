// Ships metric records to the game machine's collector (chunk 0.0 §c) as JSON lines. Same-origin POST to
// `argonia-metrics` next to the page (the sign-in gate routes it to the collector on 127.0.0.1:8091); records that
// fail stay buffered in memory and localStorage and go with the next flush; on page hide, sendBeacon.

const BACKLOG_KEY = "argonia.metrics.backlog"
const BACKLOG_MAX = 5000

export function metricsUrl(): string {
    const q = new URLSearchParams(location.search).get("argoniaMetrics")
    let stored: string | null = null
    try { stored = localStorage.getItem("argonia.metricsUrl") } catch { /* storage blocked */ }
    return new URL(q || stored || "argonia-metrics", location.href).toString()
}

export class Sink {
    private queue: string[] = []
    private inFlight = false
    readonly url = metricsUrl()
    sent = 0
    failed = 0
    lastError: string | null = null

    constructor(flushMs = 2000) {
        try {
            const old = JSON.parse(localStorage.getItem(BACKLOG_KEY) || "[]")
            if (Array.isArray(old)) this.queue.push(...old.filter((l) => typeof l === "string"))
            localStorage.removeItem(BACKLOG_KEY)
        } catch { /* nothing kept */ }
        setInterval(() => void this.flush(), flushMs)
        const bye = () => this.beacon()
        window.addEventListener("pagehide", bye)
        document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") bye() })
    }

    push(record: object) {
        this.queue.push(JSON.stringify(record))
        if (this.queue.length > BACKLOG_MAX) this.queue.splice(0, this.queue.length - BACKLOG_MAX)
    }

    async flush(): Promise<void> {
        if (this.inFlight || this.queue.length === 0) return
        this.inFlight = true
        const batch = this.queue.splice(0, 500)
        try {
            // text/plain keeps a cross-origin override free of a CORS preflight
            const r = await fetch(this.url, { method: "POST", body: batch.join("\n") + "\n", headers: { "Content-Type": "text/plain" }, keepalive: batch.length < 100, credentials: "same-origin" })
            if (!r.ok) throw new Error(`HTTP ${r.status}`)
            this.sent += batch.length
            this.lastError = null
            if (this.queue.length === 0) this.clearPersist(); else this.persist()
        } catch (e) {
            this.queue.unshift(...batch)
            this.failed++
            this.lastError = String(e)
            this.persist()
        } finally {
            this.inFlight = false
        }
    }

    private beacon() {
        if (this.queue.length === 0) return
        const body = new Blob([this.queue.join("\n") + "\n"], { type: "text/plain" })
        if (navigator.sendBeacon && navigator.sendBeacon(this.url, body)) { this.sent += this.queue.length; this.queue = []; this.clearPersist() }
        else this.persist()
    }

    private persist() { try { localStorage.setItem(BACKLOG_KEY, JSON.stringify(this.queue.slice(-BACKLOG_MAX))) } catch { /* full or blocked */ } }
    private clearPersist() { try { localStorage.removeItem(BACKLOG_KEY) } catch { /* blocked */ } }
}

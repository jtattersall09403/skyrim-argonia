// Offline check of argonia.js (chunk 0.0 §c): serves build/static plus local.html and a collector stub, drives
// headless Chrome with keyboard and touch-gamepad presses, and checks the press-to-screen samples the page paired
// against the harness host's fixed 30 ms delay, plus the layout stills for the three Magic V5 shapes.
//   node e2e/local.mjs     (after build.sh; puppeteer under build/e2e)
import fs from "node:fs"
import http from "node:http"
import path from "node:path"
import { createRequire } from "node:module"

const here = path.dirname(new URL(import.meta.url).pathname)
const out = path.join(here, "../build/e2e")
const statics = path.join(here, "../build/static")
const puppeteer = createRequire(path.join(out, "package.json"))("puppeteer")
const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const lines = []
const server = http.createServer((req, res) => {
    if (req.url.startsWith("/argonia-metrics/marker")) { res.end(JSON.stringify({ screenWidth: 1920, screenHeight: 1080, half: 24 })); return }
    if (req.url.startsWith("/argonia-metrics")) {
        let b = ""; req.on("data", (d) => (b += d)); req.on("end", () => { lines.push(...b.split("\n").filter(Boolean).map((l) => JSON.parse(l))); res.writeHead(204); res.end() }); return
    }
    const f = req.url.startsWith("/local.html") ? path.join(here, "local.html") : path.join(statics, path.normalize(req.url.split("?")[0]).replace(/^(\.\.[/\\])+/, ""))
    fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end() } else { res.writeHead(200, { "Content-Type": f.endsWith(".js") ? "text/javascript" : "text/html" }); res.end(d) } })
}).listen(18099, "127.0.0.1")
const browser = await puppeteer.launch({ headless: true, args: ["--autoplay-policy=no-user-gesture-required", "--no-sandbox"] })
let failed = []
try {
    const page = await browser.newPage()
    page.on("pageerror", (e) => console.log("pageerror", e.message))
    await page.setViewport({ width: 914, height: 408, hasTouch: true, deviceScaleFactor: 1 })
    await page.goto("http://localhost:18099/local.html?argoniaTouch=1&setup=local-harness", { waitUntil: "load" })
    await wait(1500)
    await page.focus("#input")
    for (let i = 0; i < 10; i++) { await page.keyboard.down("ControlLeft"); await wait(50); await page.keyboard.up("ControlLeft"); await wait(400) }
    const centre = (id) => page.$eval(`#argonia-touch [data-id="${id}"]`, (el) => { const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })
    for (const id of ["a", "b", "x", "y", "rt", "lt", "rb", "lb", "r3", "l3"]) { const c = await centre(id); await page.touchscreen.tap(c.x, c.y); await wait(400) }
    // left stick: hold a drag and read the pad the way upstream does
    const z = await page.$eval('#argonia-touch .at-zone[data-side="left"]', (el) => { const r = el.getBoundingClientRect(); return { x: r.x + r.width * 0.6, y: r.y + r.height * 0.6 } })
    await page.touchscreen.touchStart(z.x, z.y); await page.touchscreen.touchMove(z.x + 30, z.y - 200); await wait(100)
    const stick = await page.evaluate(() => navigator.getGamepads().find((p) => p && p.id.startsWith("Argonia"))?.axes)
    await page.touchscreen.touchEnd()
    // two fingers at once: right stick held while A is tapped
    const rz = await page.$eval('#argonia-touch .at-zone[data-side="right"]', (el) => { const r = el.getBoundingClientRect(); return { x: r.x + r.width * 0.3, y: r.y + r.height * 0.3 } })
    const cdp = await page.createCDPSession()
    const a = await centre("a")
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: rz.x, y: rz.y, id: 1 }] })
    await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: rz.x - 100, y: rz.y, id: 1 }] })
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: rz.x - 100, y: rz.y, id: 1 }, { x: a.x, y: a.y, id: 2 }] })
    await wait(30)
    const both = await page.evaluate(() => { const g = navigator.getGamepads().find((p) => p && p.id.startsWith("Argonia")); return { rx: g.axes[2], a: g.buttons[0].pressed } })
    await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] })
    await wait(600)
    await page.screenshot({ path: path.join(out, "local-folded-landscape.png") })
    for (const [w, h, name] of [[905, 835, "unfolded"], [408, 914, "folded-portrait"], [844, 390, "phone-landscape"]]) {
        await page.setViewport({ width: w, height: h, hasTouch: true, deviceScaleFactor: 1 }); await wait(400)
        await page.screenshot({ path: path.join(out, `local-${name}.png`) })
    }
    const res = await page.evaluate(() => { const m = window.argonia.metrics; m.summary(true); return { samples: m.probe.samples, frames: m.probe.frames, detections: m.probe.detector.detections, host: window.hostLog.length } })
    await wait(2500)
    const p2s = res.samples.map((s) => `${s.source}:${s.what}=${s.ms}`)
    console.log(`frames ${res.frames}, host flashes ${res.host}, detected ${res.detections}, paired ${res.samples.length}`)
    console.log("samples:", p2s.join(" "))
    console.log("stick held:", JSON.stringify(stick), "two fingers:", JSON.stringify(both))
    const kinds = lines.reduce((a, l) => ((a[l.kind] = (a[l.kind] ?? 0) + 1), a), {})
    console.log("collector stub got:", JSON.stringify(kinds))
    const ms = (src) => res.samples.filter((s) => s.source === src).map((s) => s.ms).sort((x, y) => x - y)
    const med = (v) => v[Math.floor(v.length / 2)]
    for (const src of ["keyboard", "touch"]) {
        const v = ms(src)
        console.log(`${src}: n=${v.length} median=${med(v)} min=${v[0]} max=${v.at(-1)}`)
        if (v.length < 8) failed.push(`${src}: only ${v.length} of 10 paired`)
        if (!(med(v) >= 30 && med(v) <= 90)) failed.push(`${src}: median ${med(v)} not within 30-90 ms of a 30 ms host`)
    }
    if (res.detections !== res.host) failed.push(`detected ${res.detections} of ${res.host} flashes`)
    if (!stick || stick[1] > -0.9 || stick[0] <= 0) failed.push(`stick ${JSON.stringify(stick)}`)
    if (!(both.rx < -0.5 && both.a)) failed.push(`two fingers ${JSON.stringify(both)}`)
    if (!kinds.p2s || !kinds.tick || !kinds.summary || !kinds.session) failed.push("collector stub missed a record kind")
} finally {
    await browser.close(); server.close()
}
console.log(failed.length ? "LOCAL CHECK FAILED: " + failed.join("; ") : "LOCAL CHECK PASSED")
process.exitCode = failed.length ? 1 : 0

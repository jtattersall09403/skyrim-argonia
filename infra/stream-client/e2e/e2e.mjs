// End-to-end check of our client page (chunk 0.0 §c), from the build VM: headless Chrome through an SSH forward
// and a gate-like proxy logs in to Moonlight-Web, starts the Desktop stream, sends keyboard and touch-gamepad
// presses, and leaves the metrics on the game machine's collector. e2e.sh then pulls and checks them.
//   node e2e.mjs <outDir> [webrtc|websocket]       prints {"session": ...} as its last line
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { spawn, execFileSync } from "node:child_process"
import { createRequire } from "node:module"
import { startGate } from "./gate_proxy.mjs"

const here = path.dirname(new URL(import.meta.url).pathname)
const out = path.resolve(process.argv[2] ?? path.join(here, "../build/e2e"))
const transport = process.argv[3] ?? "webrtc"
fs.mkdirSync(out, { recursive: true })
const require = createRequire(path.join(out, "package.json"))
const puppeteer = require("puppeteer")
const env = Object.fromEntries([...fs.readFileSync(path.join(os.homedir(), ".argonia/secrets.env"), "utf8").matchAll(/^\s*([A-Z_]+)=(.*)$/gm)].map((m) => [m[1], m[2].trim()]))
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a)
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const ip = execFileSync(path.join(here, "../../gpu-box/run.sh"), ["ip"], { encoding: "utf8" }).trim()
const fwd = spawn("ssh", ["-i", path.join(os.homedir(), ".argonia/keys/argonia-play"), "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-N",
    "-L", "18081:127.0.0.1:8080", "-L", "18091:127.0.0.1:8091", `Administrator@${ip}`], { stdio: "inherit" })
let gate, browser
const cleanup = async () => { try { await browser?.close() } catch { } gate?.close(); fwd.kill() }
process.on("exit", () => fwd.kill())

try {
    for (let i = 0; ; i++) {
        try { if ((await fetch("http://127.0.0.1:18081/")).ok) break } catch { }
        if (i > 40) throw new Error("no SSH forward to 8080")
        await wait(250)
    }
    gate = await startGate({ port: 18080, web: 18081, collector: 18091 })
    browser = await puppeteer.launch({
        headless: true,
        args: ["--autoplay-policy=no-user-gesture-required", "--no-sandbox", "--disable-features=WebRtcHideLocalIpsWithMdns", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"],
    })
    const page = await browser.newPage()
    const consoleLog = fs.createWriteStream(path.join(out, `console-${transport}.log`))
    page.on("console", (m) => consoleLog.write(`[${m.type()}] ${m.text()}\n`))
    page.on("pageerror", (e) => consoleLog.write(`[pageerror] ${e.message}\n`))
    await page.setViewport({ width: 914, height: 408, hasTouch: true, isMobile: false, deviceScaleFactor: 1 })
    const base = "http://localhost:18080"
    await page.goto(base + "/", { waitUntil: "domcontentloaded" })
    const ids = await page.evaluate(async (user, pass) => {
        const login = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: user, password: pass }) })
        if (!login.ok) return { error: `login ${login.status}` }
        const hostsText = await (await fetch("/api/hosts")).text()
        const hostId = Number(/"host_id":\s*(\d+)/.exec(hostsText)?.[1])
        const appsText = await (await fetch(`/api/apps?host_id=${hostId}`)).text()
        return { hostId, appsText: appsText.slice(0, 2000) }
    }, env.STREAM_USER, env.STREAM_PASSWORD)
    if (ids.error) throw new Error(ids.error)
    const apps = JSON.parse(ids.appsText)
    const list = apps.apps ?? apps
    const desktop = list.find((a) => /desktop/i.test(a.title ?? a.name ?? "")) ?? list[0]
    const appId = desktop.app_id ?? desktop.id
    log(`host ${ids.hostId}, app ${appId} (${desktop.title ?? desktop.name}), transport ${transport}`)

    await page.goto(`${base}/stream.html?hostId=${ids.hostId}&appId=${appId}&setup=e2e-headless-${transport}&argoniaTouch=1&dataTransport=${transport}`, { waitUntil: "domcontentloaded" })
    const session = await page.evaluate(() => window.argonia?.metrics?.session)
    if (!session) throw new Error("argonia.js did not load on stream.html")
    log(`session ${session}`)
    // the stream: upstream's video element with decoded frames
    let ok = false
    for (let i = 0; i < 120 && !ok; i++) {
        ok = await page.evaluate(() => {
            const v = document.querySelector("video.video-stream")
            return !!v && v.videoWidth > 0 && v.currentTime > 0.5
        })
        if (!ok) await wait(500)
    }
    const state = await page.evaluate(() => ({ transport: window.argonia.metrics["transport"](), canvas: !!document.querySelector("#root canvas"), video: !!document.querySelector("video.video-stream") }))
    log(`stream decoding: ${ok}`, JSON.stringify(state))
    await page.screenshot({ path: path.join(out, `stream-${transport}-folded-landscape.png`) })
    if (!ok) throw new Error("no decoded video within 60 s")

    // keyboard presses (Ctrl: harmless on the desktop, and five Shifts would open Sticky Keys)
    await page.focus("#input").catch(() => { })
    for (let i = 0; i < 10; i++) {
        await page.keyboard.down("ControlLeft"); await wait(60); await page.keyboard.up("ControlLeft")
        await wait(700)
    }
    // touch-gamepad presses: tap A, then B, then RT (the Gamepad API pad goes through upstream to Sunshine's XInput pad)
    const centre = (id) => page.$eval(`#argonia-touch [data-id="${id}"]`, (el) => { const r = el.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 } })
    for (const id of ["a", "a", "a", "a", "b", "b", "b", "rt", "rt", "rt"]) {
        const c = await centre(id)
        await page.touchscreen.tap(c.x, c.y)
        await wait(700)
    }
    // a left-stick drag: the pad's axes while it is held
    const z = await page.$eval('#argonia-touch .at-zone[data-side="left"]', (el) => { const r = el.getBoundingClientRect(); return { x: r.x + r.width * 0.6, y: r.y + r.height * 0.6 } })
    await page.touchscreen.touchStart(z.x, z.y)
    await page.touchscreen.touchMove(z.x + 40, z.y - 80)
    await wait(200)
    const held = await page.evaluate(() => { const g = navigator.getGamepads().find((p) => p && p.id.startsWith("Argonia")); return g ? { index: g.index, axes: g.axes } : null })
    await page.touchscreen.touchEnd()
    log("left stick held:", JSON.stringify(held))
    // the folded and unfolded shapes, as stills
    await page.screenshot({ path: path.join(out, `stream-${transport}-touch.png`) })
    await page.setViewport({ width: 905, height: 835, hasTouch: true, deviceScaleFactor: 1 })
    await wait(800)
    await page.screenshot({ path: path.join(out, `stream-${transport}-unfolded.png`) })
    await page.setViewport({ width: 408, height: 914, hasTouch: true, deviceScaleFactor: 1 })
    await wait(800)
    await page.screenshot({ path: path.join(out, `stream-${transport}-folded-portrait.png`) })
    await wait(3000)
    const res = await page.evaluate(() => {
        const m = window.argonia.metrics
        m.summary(true)
        return { samples: m.probe.samples, frames: m.probe.frames, detections: m.probe.detector.detections, errors: m.probe.sampleErrors,
            sent: m.sink.sent, failed: m.sink.failed, lastError: m.sink.lastError, desktopWidth: m.probe.desktopWidth, ticks: m.ticks.length, last: m.ticks.at(-1) }
    })
    await wait(2500)
    fs.writeFileSync(path.join(out, `page-${transport}.json`), JSON.stringify(res, null, 1))
    log(`marker: ${res.frames} frames sampled, ${res.detections} flashes seen, ${res.samples.length} paired; sink sent ${res.sent}, failed ${res.failed} ${res.lastError ?? ""}`)
    log("last tick:", JSON.stringify(res.last))
    console.log(JSON.stringify({ session, held }))
} catch (e) {
    console.error("E2E FAILED:", e.message)
    process.exitCode = 1
} finally {
    await cleanup()
}

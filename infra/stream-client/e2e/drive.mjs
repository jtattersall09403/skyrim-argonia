// Drive the game through the real stream (chunk 0.0): the same sign-in and stream start as e2e.mjs, then a list
// of steps typed and pressed through Moonlight-Web, so Sunshine injects them exactly as the owner's input is.
// Used for setup (test saves through the console); journeys stay eyeless and never use this (CLAUDE.md).
//   node drive.mjs <outDir> webrtc <steps.json>        ARGONIA_DEVICE=desktop|mac|v5-unfolded|v5-folded|matepad
// Run headful under xvfb-run (drive.sh does): pointer lock and Chrome's mobile mode need a real window. Phone and
// tablet profiles use Chrome's mobile emulation, so taps are real touch events (Input.dispatchTouchEvent), not clicks.
// steps: [{"key": "Backquote"} | {"text": "coc riverwood"} | {"wait": ms} | {"shot": "name"} | {"viewport": [w, h]} | {"tap": [x, y]} | {"click": "css"}
//          | {"down": key} | {"up": key} | {"shots": [name, count, ms]}]
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
// Never cut into the owner's session: a drive restarts the game and takes Sunshine's one stream. Stop if anyone
// is streaming (Sunshine, DCV or traffic; stream-activity.ps1), unless ARGONIA_FORCE=1.
if (!process.env.ARGONIA_FORCE) {
    const act = JSON.parse(execFileSync(path.join(here, "../../gpu-box/run.sh"),
        ["ps", ". C:\\argonia\\infra\\stream-activity.ps1; Get-StreamActivity | ConvertTo-Json -Compress"], { encoding: "utf8" }).trim())
    if (act.streaming) {
        console.log(`someone is streaming (${(act.clients ?? []).join(", ") || "traffic"}, ${act.outKbps} kbps): not driving; ARGONIA_FORCE=1 overrides`)
        process.exit(3)
    }
}
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
        headless: process.env.ARGONIA_HEADFUL ? false : true,
        defaultViewport: null,
        args: ["--autoplay-policy=no-user-gesture-required", "--no-sandbox", "--disable-features=WebRtcHideLocalIpsWithMdns", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"],
    })
    const page = await browser.newPage()
    const consoleLog = fs.createWriteStream(path.join(out, `console-${transport}.log`))
    page.on("console", (m) => consoleLog.write(`[${m.type()}] ${m.text()}\n`))
    page.on("pageerror", (e) => consoleLog.write(`[pageerror] ${e.message}\n`))
    const DEVICES = {
        desktop: { width: 1600, height: 900, deviceScaleFactor: 1, isMobile: false, hasTouch: false },
        mac: { width: 1470, height: 836, deviceScaleFactor: 2, isMobile: false, hasTouch: false },
        "v5-unfolded": { width: 784, height: 724, deviceScaleFactor: 3, isMobile: true, hasTouch: true },   // the owner's, landscape (metrics log 2026-10-29)
        "v5-folded": { width: 970, height: 432, deviceScaleFactor: 2.45, isMobile: true, hasTouch: true },
        matepad: { width: 1400, height: 920, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
    }
    const device = process.env.ARGONIA_DEVICE ?? "v5-folded"
    const profile = { ...DEVICES[device] }
    if (process.env.ARGONIA_VIEWPORT) {   // "w,h,dpr": a size to try on the device's profile
        const [w, h, d] = process.env.ARGONIA_VIEWPORT.split(",").map(Number)
        Object.assign(profile, { width: w, height: h, deviceScaleFactor: d })
    }
    if (!DEVICES[device]) throw new Error("unknown ARGONIA_DEVICE " + device)
    if (profile.isMobile) await page.setUserAgent("Mozilla/5.0 (Linux; Android 15; PLA-AN00) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36")
    await page.setViewport(profile)
    // ARGONIA_FAKEPAD=1: a real-looking pad the browser has no standard mapping for (mapping "", like the owner's
    // GameSir X2s), connected 3 s after load; steps press it with {"probe": "__fakePad.press(0, 150)"}
    if (process.env.ARGONIA_FAKEPAD) await page.evaluateOnNewDocument(() => {
        const buttons = Array.from({ length: 17 }, () => ({ pressed: false, touched: false, value: 0 }))
        const pad = { id: "GameSir-X2s (Vendor: 3537 Product: 1010)", index: 0, connected: false, mapping: "", timestamp: 0, axes: [0, 0, 0, 0], buttons, vibrationActuator: null }
        Object.defineProperty(navigator, "getGamepads", { configurable: true, writable: true, value: () => [pad.connected ? { ...pad, buttons: buttons.map((b) => ({ ...b })), axes: pad.axes.slice() } : null] })
        window.__fakePad = {
            press(i, ms) { buttons[i] = { pressed: true, touched: true, value: 1 }; pad.timestamp = performance.now(); setTimeout(() => { buttons[i] = { pressed: false, touched: false, value: 0 }; pad.timestamp = performance.now() }, ms); return i },
            axis(i, v) { pad.axes[i] = v; pad.timestamp = performance.now(); return v },
        }
        setTimeout(() => { pad.connected = true; const ev = new Event("gamepadconnected"); Object.defineProperty(ev, "gamepad", { value: { ...pad } }); window.dispatchEvent(ev) }, 3000)
    })
    log("device", device, JSON.stringify(profile))
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
    const want = new RegExp(process.env.ARGONIA_APP ?? "desktop", "i")  // which Sunshine app to start
    const desktop = list.find((a) => want.test(a.title ?? a.name ?? "")) ?? list[0]
    const appId = desktop.app_id ?? desktop.id
    log(`host ${ids.hostId}, app ${appId} (${desktop.title ?? desktop.name}), transport ${transport}`)

    // Sunshine runs one app at a time and a new session resumes whatever is running (the Desktop never ends by
    // itself), so quit it first when asked.
    if (process.env.ARGONIA_CANCEL) {
        const c = await page.evaluate(async (hostId) => (await fetch("/api/host/cancel", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ host_id: hostId }) })).status, ids.hostId)
        log("cancelled the running app:", c)
        await wait(3000)
    }
    await page.goto(`${base}/stream.html?hostId=${ids.hostId}&appId=${appId}&setup=drive-headless-${transport}&dataTransport=${transport}`, { waitUntil: "domcontentloaded" })
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
    await page.screenshot({ path: path.join(out, `drive-start.png`) })
    if (!ok) throw new Error("no decoded video within 60 s")

    const steps = JSON.parse(fs.readFileSync(process.argv[4], "utf8"))
    await page.focus("#input").catch(() => { })
    for (const s of steps) {
        if (s.key) { await page.keyboard.down(s.key); await wait(80); await page.keyboard.up(s.key); await wait(250) }
        else if (s.down) { await page.keyboard.down(s.down) }
        else if (s.up) { await page.keyboard.up(s.up) }
        else if (s.shots) { for (let i = 0; i < s.shots[1]; i++) { await page.screenshot({ path: path.join(out, `drive-${s.shots[0]}-${i}.png`) }); await wait(s.shots[2] ?? 150) } }
        else if (s.text) { for (const ch of s.text) { await page.keyboard.type(ch); await wait(90) } }
        else if (s.wait) await wait(s.wait)
        else if (s.tap) {   // a real touch tap: on an element (css) or at [x, y]
            let x, y
            if (typeof s.tap === "string") {
                const r = await page.$eval(s.tap, (el) => { const b = el.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 } }).catch(() => null)
                if (!r) { log("tap: no element", s.tap); continue }
                x = r.x; y = r.y
            } else { [x, y] = s.tap }
            await page.touchscreen.tap(x, y); await wait(400)
        }
        else if (s.look) {   // relative mouse movement in steps (the camera): [dx, dy, steps]
            const [dx, dy, n = 10] = s.look
            const c = page.viewport() ?? { width: 800, height: 600 }
            let x = c.width / 2, y = c.height / 2
            for (let i = 0; i < n; i++) { x += dx / n; y += dy / n; await page.mouse.move(x, y); await wait(30) }
        }
        else if (s.probe) { log("probe", s.probe, JSON.stringify(await page.evaluate(s.probe))) }
        else if (s.click) { await page.click(s.click).catch((e) => log("click failed", s.click, e.message)); await wait(600) }
        else if (s.viewport) { await page.setViewport({ width: s.viewport[0], height: s.viewport[1], hasTouch: true, deviceScaleFactor: 1 }); await wait(1500) }
        else if (s.shot) { await page.screenshot({ path: path.join(out, `drive-${s.shot}.png`) }); log("shot", s.shot) }
    }
    log("steps done")
} catch (e) {
    log("DRIVE FAILED:", e.message); process.exitCode = 1
} finally {
    await cleanup()
}

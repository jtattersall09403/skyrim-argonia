// The play switch (owner call #6): a Cloudflare Worker on play.<domain> (and dcv., sunshine.), behind Cloudflare
// Access, for the one play machine, argonia-play (eu-west-3, g4dn.xlarge on demand, decision 0039), whose own hostname is
// play-<ORIGIN_LABEL>.<domain> (behind Access with the switch's service token).
// - A page load goes to the machine if it runs: the Worker forwards the request to its own hostname.
// - Stopped: it starts it and shows a page that reloads into the stream once it is up (a settling refusal retries).
// - /argonia/stop stops it; /argonia/status reports it.
// - Cost backstops (scheduled every 10 min): stop it when it has run longer than MAX_HOURS, when its heartbeat
//   (idle-stop.ps1, at /argonia-metrics/activity) has been missing or stale STALE_MINUTES after its start, and
//   every night at NIGHT_STOP; an agent's fresh "agent job" beat spares it from the cap and the night stop.
//   Idle with a live heartbeat is the machine's own idle-stop's job (15 minutes).
// Bindings: AWS_KEY_ID, AWS_SECRET (an IAM user that may start and stop only the play instance);
// REGION (default eu-west-3), NAME (default argonia-play), ORIGIN_LABEL (default paris); DOMAIN; CF_TOKEN, CF_ZONE,
// HOST_NAME keep host.<domain> (DNS only) on the machine for the Moonlight app; CF_ACCESS_ID, CF_ACCESS_SECRET (an
// Access service token) pass the machine's own gates. Deployed by infra/gpu-box/cloudflare_gate.py worker.

const MAX_HOURS = 8
const STALE_MINUTES = 30
const NAME = "argonia-play"
const REGION = "eu-west-3"   // g4dn.xlarge on demand (decision 0039)

/** Stop for a dead heartbeat? Only once the machine has been up STALE_MINUTES, so a boot is never cut short, and
 *  only on time since this start: the old traffic alarm counted quiet minutes from before a stop. */
export function heartbeatStop(launchedMs, nowMs, beatUtc) {
  if (!launchedMs || nowMs - launchedMs < STALE_MINUTES * 60e3) return false
  const beat = beatUtc ? Date.parse(beatUtc) : NaN
  return !(beat > nowMs - STALE_MINUTES * 60e3)
}

/** Is an agent working on the machine (a deploy or batch over SSH, or the bridge's busy flag), by a fresh beat?
 *  The night stop and the MAX_HOURS cap spare it, and the owner is never sent to it.
 *  A stream alone does not count, so a forgotten stream still stops at night. */
export function agentBusy(nowMs, beat) {
  const t = beat?.utc ? Date.parse(beat.utc) : NaN
  if (!(t > nowMs - 12 * 60e3)) return false
  // "agent command running (n)": a command outliving the 15-minute busy flag (idle-stop.ps1's hold, 2026-11-06)
  return (beat.why || []).some((w) => w === "agent ssh" || w === "agent job" || String(w).startsWith("agent command running"))
}

/** A Start refused while the spot request or the instance is still settling after a stop (owner #29), or for no spot
 *  capacity: the page says "starting…" and tries again at each reload (4 s)
 *  for up to START_RETRY_MS from the first refusal, which a cookie carries. */
export const START_RETRY_MS = 120e3
const SETTLING = /IncorrectSpotRequestState|IncorrectInstanceState|InsufficientInstanceCapacity/
export function startRetry(error, firstMs, nowMs) {
  if (!SETTLING.test(String(error))) return false
  return !firstMs || nowMs - firstMs < START_RETRY_MS
}
const RETRY_COOKIE = "argoniaStartRetry"

const cookieOf = (request, name) => new RegExp(`(?:^|;\\s*)${name}=([^;]*)`).exec(request?.headers.get("cookie") || "")?.[1]
const LABEL = "Paris"

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const m = await machineState(env)
    if (url.pathname === "/argonia/status") return json({ ...m, beat: m.state === "running" ? await beatOf(env, m) : null })
    if (url.pathname === "/argonia/stop") {
      if (m.state === "running") await ec2(env, m.region, { Action: "StopInstances", "InstanceId.1": m.id })
      cached = null
      return page(m.state === "running" ? `Stopping ${LABEL}` : "Nothing to stop", "It is switching off. Nothing is charged while it is off.", false)
    }
    // Only a page load starts the machine: the heartbeat read and a stale tab's metrics posts must not
    // (a heartbeat check through the gate started it, 2026-10-29).
    if (url.pathname === "/argonia/start" || m.state !== "running" && m.state !== "pending") {
      if (url.pathname.startsWith("/argonia-metrics")) return json({ error: "no game machine is on" }, 503)
      return startPage(env, request, m)
    }
    if (m.ip) await syncHost(env, m.ip)
    let res = null
    if (m.state === "running") {
      try { res = await forward(request, env, m) } catch (e) { res = null }
    }
    if (!res || res.status === 530 || res.status === 502 || res.status === 1033) {
      if (url.pathname.startsWith("/argonia-metrics")) return json({ error: `${LABEL} is starting` }, 503)
      res = m.state === "running" ? page(`${LABEL} is on; its desktop is starting`, "Usually under two minutes.", true)
                                  : page(`Starting ${LABEL}`, "Usually under a minute. This page turns into the stream as soon as it is ready.", true)
    }
    return res
  },

  async scheduled(event, env) {
    const m = await machineState(env)
    if (m.state !== "running") return
    const hours = (Date.now() - Date.parse(m.launched)) / 3.6e6
    const beat = await beatOf(env, m)
    const capped = (event.cron === env.NIGHT_STOP || hours > MAX_HOURS) && !agentBusy(Date.now(), beat)
    if (capped || heartbeatStop(Date.parse(m.launched), Date.now(), beat?.utc))
      await ec2(env, m.region, { Action: "StopInstances", "InstanceId.1": m.id })
  },
}

/** The machine's own hostname for this request's page (play. -> play-paris.). */
export function originHost(host, label, domain) {
  const prefix = host.split(".")[0]
  return `${prefix}-${label}.${domain}`
}

// The request, sent on to the machine's own hostname past its gate with the service token. One sign-in only (owner,
// 2026-10-29): Moonlight-Web serves its default user to anyone without a session, and only the owner gets past
// Access, but a stale or expired mlSession cookie makes it ask for a login instead, so that cookie never reaches it;
// nor does the owner's Access cookie for play., which is not the machine's app.
async function forward(request, env, m) {
  const url = new URL(request.url)
  const host = url.hostname
  url.hostname = originHost(host, env.ORIGIN_LABEL || "paris", env.DOMAIN)
  const headers = new Headers(request.headers)
  const cookie = request.headers.get("cookie")
  if (cookie) {
    const rest = cookie.split(/;\s*/).filter((c) => !/^(mlSession|CF_Authorization|argonia\w*)=/.test(c)).join("; ")
    if (rest) headers.set("cookie", rest); else headers.delete("cookie")
  }
  if (env.CF_ACCESS_ID) { headers.set("CF-Access-Client-Id", env.CF_ACCESS_ID); headers.set("CF-Access-Client-Secret", env.CF_ACCESS_SECRET) }
  const res = await fetch(new Request(url.toString(), new Request(request, { headers, redirect: "manual" })))
  const loc = res.headers.get("location")
  if (loc && loc.includes(url.hostname)) {
    const out = new Response(res.body, res)
    out.headers.set("location", loc.replace(url.hostname, host))
    return out
  }
  return res
}

// The running machine's heartbeat through its own hostname, past Access with the service token; null if it does not
// answer. Not configured: never stop on it.
async function beatOf(env, m) {
  if (!env.CF_ACCESS_ID) return { utc: new Date().toISOString() }
  try {
    const r = await fetch(`https://${originHost("play.x", env.ORIGIN_LABEL || "paris", env.DOMAIN)}/argonia-metrics/activity`,
      { headers: { "CF-Access-Client-Id": env.CF_ACCESS_ID, "CF-Access-Client-Secret": env.CF_ACCESS_SECRET } })
    return r.ok ? await r.json() : null
  } catch { return null }
}

async function startPage(env, request, m) {
  const first = Number(cookieOf(request, RETRY_COOKIE)) || 0
  if (m.state === "stopping") return page("The game machine is still switching off", "Give it a minute; this page will start it again.", true)
  if (m.state !== "stopped") return page("The game machine is not set up", "No instance named " + (env.NAME || NAME) + " exists.", true)
  try {
    await ec2(env, m.region, { Action: "StartInstances", "InstanceId.1": m.id })
    cached = null
  } catch (e) {
    const err = String(e.message).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").slice(0, 200)
    const now = Date.now()
    if (startRetry(String(e.message), first, now)) {
      const res = page("Starting\u2026", "AWS has no room for the machine this moment, or is still settling it after its stop; this page keeps trying for two minutes.", true)
      if (!first) res.headers.append("set-cookie", `${RETRY_COOKIE}=${now}; Path=/; Max-Age=300; Secure`)
      return res
    }
    const res = page("No game machine could start", `AWS said: ${err}`, false)
    res.headers.append("set-cookie", `${RETRY_COOKIE}=; Path=/; Max-Age=0; Secure`)
    return res
  }
  const res = page(`Starting ${LABEL}`, (m.reclaimed ? RECLAIMED_TEXT + " " : "") +
    "Usually under a minute. This page turns into the stream as soon as it is ready.", true)
  res.headers.append("set-cookie", `${RETRY_COOKIE}=; Path=/; Max-Age=0; Secure`)
  return res
}

// host.<domain> follows the machine's public IP (an A record, not proxied: the Moonlight app needs the real address).
async function syncHost(env, ip) {
  if (!env.CF_TOKEN || !env.CF_ZONE || !env.HOST_NAME) return
  const api = `https://api.cloudflare.com/client/v4/zones/${env.CF_ZONE}/dns_records`
  const h = { authorization: `Bearer ${env.CF_TOKEN}`, "content-type": "application/json" }
  const found = (await (await fetch(`${api}?type=A&name=${env.HOST_NAME}`, { headers: h })).json()).result?.[0]
  if (found?.content === ip) return
  const body = JSON.stringify({ type: "A", name: env.HOST_NAME, content: ip, ttl: 60, proxied: false })
  await fetch(found ? `${api}/${found.id}` : api, { method: found ? "PUT" : "POST", headers: h, body })
}

function page(title, text, refresh) {
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
${refresh ? '<meta http-equiv="refresh" content="4">' : ""}<title>${title}</title>
<style>body{font:18px system-ui,sans-serif;background:#141a14;color:#e8e4d8;display:grid;place-items:center;min-height:100vh;margin:0;padding:16px;box-sizing:border-box}
main{max-width:30em;text-align:center}a{color:#c9b67a}.stop{display:inline-block;margin-top:2em;padding:.6em 1.2em;border:1px solid #c9b67a;border-radius:8px;text-decoration:none}</style>
</head><body><main><h1>${title}</h1><p>${text}</p><a class="stop" href="/argonia/stop">Stop the game machine now</a></main></body></html>`
  return new Response(html, { status: 503, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "retry-after": "4" } })
}

function json(o, status = 200) { return new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } }) }

/** The machine's state (DescribeInstances by its Name in its region), with its build stamp and spot status;
 *  kept 5 s in the isolate, so a page's burst of requests asks AWS once. */
let cached = null
async function machineState(env) {
  if (cached && cached.env === env && Date.now() - cached.t < 5e3) return cached.m
  const m = await describe(env)
  cached = { env, t: Date.now(), m }
  return m
}
async function describe(env) {
  const region = env.REGION || REGION, name = env.NAME || NAME
  const xml = await ec2(env, region, { Action: "DescribeInstances", "Filter.1.Name": "tag:Name", "Filter.1.Value.1": name,
    // never a terminated or shutting-down instance that still carries the name (a cut-over leaves one)
    "Filter.2.Name": "instance-state-name", "Filter.2.Value.1": "pending", "Filter.2.Value.2": "running", "Filter.2.Value.3": "stopping", "Filter.2.Value.4": "stopped" })
  const s = { name, region, ...parseInstance(xml) }
  if (s.spot && s.state !== "running") {  // why it stopped, if AWS stopped it (1.8 §2)
    try { s.spotStatus = spotStatus(await ec2(env, region, { Action: "DescribeSpotInstanceRequests", "SpotInstanceRequestId.1": s.spot })) } catch { s.spotStatus = null }
    s.reclaimed = reclaimed(s.state, s.spotStatus)
  }
  return s
}

/** The first instance of a DescribeInstances answer: id, state, launch time, public IP, spot request id, build. */
export function parseInstance(xml) {
  const items = [...xml.matchAll(/<instancesSet>([\s\S]*?)<\/instancesSet>/g)].map((m) => m[1]).join("")
  const id = /<instanceId>(i-[0-9a-f]+)<\/instanceId>/.exec(items)?.[1]
  const st = /<instanceState>[\s\S]*?<name>([a-z-]+)<\/name>/.exec(items)?.[1] ?? "missing"
  const launched = /<launchTime>([^<]+)<\/launchTime>/.exec(items)?.[1] ?? null
  const ip = /<ipAddress>([0-9.]+)<\/ipAddress>/.exec(items)?.[1] ?? null
  const spot = /<spotInstanceRequestId>(sir-[0-9a-z]+)<\/spotInstanceRequestId>/.exec(items)?.[1] ?? null
  // the build a deploy left on it (deploy.sh tags argonia-build and argonia-build-utc at DEPLOY OK)
  const tag = (k) => new RegExp(`<key>${k}</key>\\s*<value>([^<]*)</value>`).exec(items)?.[1] ?? null
  return { id, state: st, launched, ip, spot, build: tag("argonia-build"), buildUtc: tag("argonia-build-utc") }
}

/** A DescribeSpotInstanceRequests answer's status code (e.g. marked-for-stop, instance-stopped-no-capacity). */
export function spotStatus(xml) { return /<status>[\s\S]*?<code>([a-z-]+)<\/code>/.exec(xml)?.[1] ?? null }

/** Did AWS take the machine back (not the owner, idle-stop or a cap)? Then the page says so: spot-watch.ps1 wrote
 *  the suspend save on the two-minute notice. */
export function reclaimed(state, code) {
  if (!code || state === "running" || state === "pending") return code === "marked-for-stop"
  return code === "marked-for-stop" || code.startsWith("instance-stopped-") && code !== "instance-stopped-by-user"
}

export const RECLAIMED_TEXT = "AWS took the machine back; your game was saved."

async function ec2(env, REGION, params) {
  const host = `ec2.${REGION}.amazonaws.com`
  const q = new URLSearchParams({ ...params, Version: "2016-11-15" })
  const query = [...q.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([k, v]) => `${enc(k)}=${enc(v)}`).join("&")
  const now = new Date().toISOString().replace(/[:-]|\.\d{3}/g, "")
  const day = now.slice(0, 8)
  // A session token (temporary credentials) is optional: the Worker uses a long-lived key; tests use a role's.
  const tok = env.AWS_SESSION_TOKEN
  const headers = tok ? `host:${host}\nx-amz-date:${now}\nx-amz-security-token:${tok}\n` : `host:${host}\nx-amz-date:${now}\n`
  const signed = tok ? "host;x-amz-date;x-amz-security-token" : "host;x-amz-date"
  const canonical = ["GET", "/", query, headers, signed, await hex(await sha256(""))].join("\n")
  const scope = `${day}/${REGION}/ec2/aws4_request`
  const toSign = ["AWS4-HMAC-SHA256", now, scope, await hex(await sha256(canonical))].join("\n")
  let key = await hmac(new TextEncoder().encode("AWS4" + env.AWS_SECRET), day)
  for (const part of [REGION, "ec2", "aws4_request"]) key = await hmac(key, part)
  const sig = await hex(await hmac(key, toSign))
  const auth = `AWS4-HMAC-SHA256 Credential=${env.AWS_KEY_ID}/${scope}, SignedHeaders=${signed}, Signature=${sig}`
  const h = { "x-amz-date": now, authorization: auth }
  if (tok) h["x-amz-security-token"] = tok
  const r = await fetch(`https://${host}/?${query}`, { headers: h })
  const body = await r.text()
  if (!r.ok) throw new Error(`EC2 ${params.Action} ${r.status}: ${body.slice(0, 300)}`)
  return body
}
const enc = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => "%" + c.charCodeAt(0).toString(16).toUpperCase())
async function sha256(s) { return crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)) }
async function hmac(key, s) {
  const k = await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"])
  return new Uint8Array(await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(s)))
}
async function hex(buf) { return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("") }

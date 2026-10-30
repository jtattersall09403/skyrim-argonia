// The play switch (owner call #6): a Cloudflare Worker on play.<domain> and dcv.<domain>, behind Cloudflare Access.
// - Machine on: requests pass straight through the tunnel to the stream pages.
// - Machine off (the tunnel answers 530): the Worker starts argonia-play and shows a page that reloads into the
//   stream once it is up. /argonia/stop stops it; /argonia/status reports it.
// - Cost backstops, independent of the machine (scheduled every 10 min): stop it if it has run longer than
//   MAX_HOURS, if its heartbeat (idle-stop.ps1, served at /argonia-metrics/activity) has been missing or stale for
//   STALE_MINUTES while it has been up that long (Windows hung, or idle-stop broken), and every night at the
//   NIGHT_STOP cron. Idle with a live heartbeat is the machine's own idle-stop's job.
// Secrets (Worker bindings): AWS_KEY_ID, AWS_SECRET (an IAM user allowed only to describe, start and stop
// Name=argonia-play); CF_TOKEN, CF_ZONE, HOST_NAME keep host.<domain> (DNS only) on the machine's public IP for
// the Moonlight app, whose address changes at every start; CF_ACCESS_ID, CF_ACCESS_SECRET (an Access service
// token) let the heartbeat read pass the sign-in gate. Deployed by infra/gpu-box/cloudflare_gate.py worker.

const REGION = "eu-west-2"
const NAME = "argonia-play"
const MAX_HOURS = 8
const STALE_MINUTES = 30

/** Stop for a dead heartbeat? Only once the machine has been up STALE_MINUTES, so a boot is never cut short, and
 *  only on time since this start: the old traffic alarm counted quiet minutes from before a stop. */
export function heartbeatStop(launchedMs, nowMs, beatUtc) {
  if (!launchedMs || nowMs - launchedMs < STALE_MINUTES * 60e3) return false
  const beat = beatUtc ? Date.parse(beatUtc) : NaN
  return !(beat > nowMs - STALE_MINUTES * 60e3)
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    if (url.pathname === "/argonia/status") {
      const s = await state(env)
      if (s.ip) await syncHost(env, s.ip)
      return json(s)
    }
    if (url.pathname === "/argonia/stop") {
      const s = await state(env)
      if (s.state === "running" || s.state === "pending") await ec2(env, { Action: "StopInstances", "InstanceId.1": s.id })
      return page("Stopping the game machine", "It is switching off. Nothing is charged while it is off.", false)
    }
    if (url.pathname === "/argonia/start") return startPage(env)
    // One sign-in only (owner, 2026-10-29): Moonlight-Web serves its default user to anyone without a session, and
    // only the owner gets past Access, but a stale or expired mlSession cookie makes it ask for a login instead.
    // So the cookie never reaches it.
    let req = request
    const cookie = request.headers.get("cookie")
    if (cookie && /(^|;\s*)mlSession=/.test(cookie)) {
      const headers = new Headers(request.headers)
      const rest = cookie.split(/;\s*/).filter((c) => !c.startsWith("mlSession=")).join("; ")
      if (rest) headers.set("cookie", rest); else headers.delete("cookie")
      req = new Request(request, { headers })
    }
    let res
    try { res = await fetch(req) } catch (e) { res = null }
    if (res && res.status !== 530 && res.status !== 502 && res.status !== 1033) return res
    // Only a page load starts the machine: the heartbeat read and a stale tab's metrics posts must not
    // (a heartbeat check through the gate started it, 2026-10-29).
    if (url.pathname.startsWith("/argonia-metrics")) return json({ error: "the game machine is off" }, 503)
    return startPage(env)
  },

  async scheduled(event, env) {
    const s = await state(env)
    if (s.ip) await syncHost(env, s.ip)
    if (s.state !== "running") return
    const hours = (Date.now() - Date.parse(s.launched)) / 3.6e6
    const beat = await heartbeat(env)
    if (event.cron === env.NIGHT_STOP || hours > MAX_HOURS || heartbeatStop(Date.parse(s.launched), Date.now(), beat?.utc))
      await ec2(env, { Action: "StopInstances", "InstanceId.1": s.id })
  },
}

// The machine's heartbeat through the tunnel, past Access with the service token; null if it does not answer.
async function heartbeat(env) {
  if (!env.CF_ACCESS_ID || !env.ACTIVITY_URL) return { utc: new Date().toISOString() }   // not configured: never stop on it
  try {
    const r = await fetch(env.ACTIVITY_URL, { headers: { "CF-Access-Client-Id": env.CF_ACCESS_ID, "CF-Access-Client-Secret": env.CF_ACCESS_SECRET } })
    return r.ok ? await r.json() : null
  } catch { return null }
}

async function startPage(env) {
  const s = await state(env)
  if (s.ip) await syncHost(env, s.ip)
  if (s.state === "stopped") {
    await ec2(env, { Action: "StartInstances", "InstanceId.1": s.id })
    return page("Starting the game machine", "Usually under a minute. This page turns into the stream as soon as it is ready.", true)
  }
  if (s.state === "stopping") return page("The game machine is still switching off", "Give it a minute; this page will start it again.", true)
  if (s.state === "running") return page("The game machine is on; its desktop is starting", "Usually under two minutes.", true)
  return page("Starting the game machine", `It is ${s.state}. This page reloads into the stream when it is ready.`, true)
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

async function state(env) {
  const xml = await ec2(env, { Action: "DescribeInstances", "Filter.1.Name": "tag:Name", "Filter.1.Value.1": NAME,
    // never a terminated or shutting-down instance that still carries the name (a cut-over leaves one)
    "Filter.2.Name": "instance-state-name", "Filter.2.Value.1": "pending", "Filter.2.Value.2": "running", "Filter.2.Value.3": "stopping", "Filter.2.Value.4": "stopped" })
  const items = [...xml.matchAll(/<instancesSet>([\s\S]*?)<\/instancesSet>/g)].map((m) => m[1]).join("")
  const id = /<instanceId>(i-[0-9a-f]+)<\/instanceId>/.exec(items)?.[1]
  const st = /<instanceState>[\s\S]*?<name>([a-z-]+)<\/name>/.exec(items)?.[1] ?? "missing"
  const launched = /<launchTime>([^<]+)<\/launchTime>/.exec(items)?.[1] ?? null
  const ip = /<ipAddress>([0-9.]+)<\/ipAddress>/.exec(items)?.[1] ?? null
  return { id, state: st, launched, ip }
}

// EC2 Query API with Signature Version 4 (WebCrypto; no dependencies).
async function ec2(env, params) {
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

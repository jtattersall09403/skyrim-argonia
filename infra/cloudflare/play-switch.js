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
//
// The studio's address (STUDIO_HOST, studio.<domain>: the build machine's own tunnel, behind the same Access app) is
// routed here too, for its page and /argonia/*: the build machine (STUDIO_NAME, default argonia-build, in
// STUDIO_REGION, default eu-west-2) running, the request goes on to the tunnel unchanged; stopped, the owner (the
// Access sign-in's email, its token checked against the team's keys: ACCESS_TEAM, STUDIO_AUD, OWNER_EMAIL) gets a
// waiting page that turns into the studio once it answers, and the machine is started with the tag
// argonia-studio-start=<time> written first, so its boot (infra/build-vm/resume.sh) knows the studio started it and
// starts no agent. Anyone else is refused. The machine stops itself as before (idle-stop and the owner's alarm).

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
    if (env.STUDIO_HOST && url.hostname === env.STUDIO_HOST) return studio(request, env)
    const m = await machineState(env)
    if (url.pathname === "/argonia/status") return json({ ...m, beat: m.state === "running" ? await beatOf(env, m) : null })
    if (url.pathname === "/argonia/stop") {
      if (m.state === "running") await ec2(env, m.region, { Action: "StopInstances", "InstanceId.1": m.id })
      cache.clear()
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
    cache.clear()
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

function page(title, text, refresh, stop = "/argonia/stop") {
  const html = `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
${refresh ? '<meta http-equiv="refresh" content="4">' : ""}<title>${title}</title>
<style>body{font:18px system-ui,sans-serif;background:#141a14;color:#e8e4d8;display:grid;place-items:center;min-height:100vh;margin:0;padding:16px;box-sizing:border-box}
main{max-width:30em;text-align:center}a{color:#c9b67a}.stop{display:inline-block;margin-top:2em;padding:.6em 1.2em;border:1px solid #c9b67a;border-radius:8px;text-decoration:none}</style>
</head><body><main><h1>${title}</h1><p>${text}</p>${stop ? `<a class="stop" href="${stop}">Stop the game machine now</a>` : ""}</main></body></html>`
  return new Response(html, { status: 503, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "retry-after": "4" } })
}

function json(o, status = 200) { return new Response(JSON.stringify(o), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } }) }

/** A machine's state (DescribeInstances by its Name in its region), with its build stamp and spot status;
 *  kept 5 s in the isolate, so a page's burst of requests asks AWS once. The play machine unless `which` names
 *  another ({name, region}: the build machine, for the studio). */
const cache = new Map()
async function machineState(env, which = null) {
  const key = which?.name || env.NAME || NAME, hit = cache.get(key)
  if (hit && hit.env === env && Date.now() - hit.t < 5e3) return hit.m
  const m = await describe(env, which)
  cache.set(key, { env, t: Date.now(), m })
  return m
}
async function describe(env, which = null) {
  const region = which?.region || env.REGION || REGION, name = which?.name || env.NAME || NAME
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

// ---- the studio's address: the build machine ---------------------------------------------------------------------

export const STUDIO_START_TAG = "argonia-studio-start"
const studioMachine = (env) => ({ name: env.STUDIO_NAME || "argonia-build", region: env.STUDIO_REGION || "eu-west-2" })
const ORIGIN_DOWN = new Set([502, 503, 521, 522, 523, 530, 1033])

async function studio(request, env) {
  const url = new URL(request.url)
  const which = studioMachine(env), m = await machineState(env, which)
  const owner = await isOwner(request, env)
  if (url.pathname === "/argonia/status") return owner ? json({ name: m.name, state: m.state, launched: m.launched }) : json({ error: "only the owner" }, 403)
  if (m.state === "running") {
    let res = null
    try { res = await fetch(request) } catch { res = null }
    if (res && !ORIGIN_DOWN.has(res.status)) {
      const out = new Response(res.body, res)
      out.headers.set("x-argonia-switch", "studio")
      return out
    }
    return studioPage("The build machine is on; the studio is starting", "Usually under a minute. This page turns into the studio as soon as it is ready.", true)
  }
  if (!owner) return studioPage("Only the owner can start the build machine", "Sign in with the owner's email to open the studio.", false, 403)
  return studioStart(env, request, m, which)
}

/** Start the stopped build machine for the owner: the tag first (the boot reads it and starts no agent), then the
 *  start; a settling refusal retries as the play page does; any other failure says what to do. */
async function studioStart(env, request, m, which) {
  if (m.state === "pending") return studioPage("Starting the build machine", "This takes about a minute. This page turns into the studio as soon as it is ready.", true)
  if (m.state === "stopping") return studioPage("The build machine is still switching off", "Give it a minute; this page will start it again.", true)
  if (m.state !== "stopped") return studioPage("The build machine could not be found", `No instance named ${which.name} exists. Tell the agent on GitHub.`, false)
  const first = Number(cookieOf(request, RETRY_COOKIE)) || 0
  try {
    await ec2(env, m.region, { Action: "CreateTags", "ResourceId.1": m.id, "Tag.1.Key": STUDIO_START_TAG, "Tag.1.Value": new Date().toISOString() })
    await ec2(env, m.region, { Action: "StartInstances", "InstanceId.1": m.id })
    cache.clear()
  } catch (e) {
    const err = String(e.message).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 200).replace(/\.$/, "")
    const now = Date.now()
    if (startRetry(String(e.message), first, now)) {
      const res = studioPage("Starting…", "AWS is still settling the build machine after its stop; this page keeps trying for two minutes.", true)
      if (!first) res.headers.append("set-cookie", `${RETRY_COOKIE}=${now}; Path=/; Max-Age=300; Secure`)
      return res
    }
    const res = studioPage("The build machine could not start",
      `AWS said: ${err}. Try again in a few minutes by reloading this page. If it still fails, start argonia-build ` +
      "from the AWS console (EC2, London, Instances, Instance state, Start) and tell the agent on GitHub.", false)
    res.headers.append("set-cookie", `${RETRY_COOKIE}=; Path=/; Max-Age=0; Secure`)
    return res
  }
  const res = studioPage("Starting the build machine", "This takes about a minute. This page turns into the studio as soon as it is ready.", true)
  res.headers.append("set-cookie", `${RETRY_COOKIE}=; Path=/; Max-Age=0; Secure`)
  return res
}

function studioPage(title, text, refresh, status = 503) {
  const res = page(title, text, refresh, null)
  return new Response(res.body, { status, headers: res.headers })
}

/** Is this request the owner's? The Access sign-in's token (the header Access adds, else its cookie), checked
 *  against the team's signing keys, for this app, unexpired, with the owner's email. Not configured: no one. */
export async function isOwner(request, env, nowMs = Date.now()) {
  if (!env.ACCESS_TEAM || !env.STUDIO_AUD || !env.OWNER_EMAIL) return false
  const tok = request.headers.get("cf-access-jwt-assertion") || cookieOf(request, "CF_Authorization")
  const claims = tok ? await verifiedClaims(tok, env, nowMs) : null
  const aud = [].concat(claims?.aud || [])
  return !!claims && aud.includes(env.STUDIO_AUD) && claims.iss === `https://${env.ACCESS_TEAM}` &&
    String(claims.email || "").toLowerCase() === env.OWNER_EMAIL.toLowerCase()
}

const b64url = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0))
let certs = null
async function verifiedClaims(tok, env, nowMs) {
  try {
    const [h, p, sig] = tok.split(".")
    const head = JSON.parse(new TextDecoder().decode(b64url(h)))
    const claims = JSON.parse(new TextDecoder().decode(b64url(p)))
    if (head.alg !== "RS256" || !(claims.exp * 1000 > nowMs)) return null
    if (!certs || certs.team !== env.ACCESS_TEAM || nowMs - certs.t > 3600e3 || !certs.keys.some((k) => k.kid === head.kid))
      certs = { team: env.ACCESS_TEAM, t: nowMs, keys: (await (await fetch(`https://${env.ACCESS_TEAM}/cdn-cgi/access/certs`)).json()).keys || [] }
    const jwk = certs.keys.find((k) => k.kid === head.kid)
    if (!jwk) return null
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"])
    const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(sig), new TextEncoder().encode(`${h}.${p}`))
    return ok ? claims : null
  } catch { return null }
}

/** The studio start's two AWS calls as dry runs (EC2's DryRun), for a check that changes nothing: each says
 *  "would succeed" or AWS's refusal. */
export async function studioDryRun(env) {
  const which = studioMachine(env), m = await describe(env, which)
  const out = { name: m.name, id: m.id, state: m.state }
  for (const [k, params] of [["tag", { Action: "CreateTags", "ResourceId.1": m.id, "Tag.1.Key": STUDIO_START_TAG, "Tag.1.Value": "dry-run" }],
                             ["start", { Action: "StartInstances", "InstanceId.1": m.id }]]) {
    try { await ec2(env, m.region, { ...params, DryRun: "true" }); out[k] = "succeeded (not a dry run?)" }
    catch (e) { const code = /<Code>([^<]+)<\/Code>/.exec(e.message)?.[1] || String(e.message).slice(0, 120); out[k] = code === "DryRunOperation" ? "would succeed" : code }
  }
  return out
}

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

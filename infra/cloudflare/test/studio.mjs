// The studio's address on the play switch, without AWS or Cloudflare:   node infra/cloudflare/test/studio.mjs
// The owner with the build machine stopped (tagged, started, the waiting page), the owner with it up (the request goes
// on to the tunnel), not the owner (refused, nothing started), and a start AWS refuses (a plain message, what to do).
import assert from "node:assert/strict"
import worker, { isOwner, STUDIO_START_TAG } from "../play-switch.js"

const TEAM = "argonia.cloudflareaccess.com", AUD = "studio-aud", OWNER = "owner@example.com", HOST = "studio.example.com"
const keys = await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"])
const jwk = { ...(await crypto.subtle.exportKey("jwk", keys.publicKey)), kid: "k1", alg: "RS256" }
const b64 = (b) => Buffer.from(b).toString("base64url")
async function token(claims, kid = "k1", key = keys.privateKey) {
  const head = b64(JSON.stringify({ alg: "RS256", kid })), body = b64(JSON.stringify(claims))
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(`${head}.${body}`))
  return `${head}.${body}.${b64(sig)}`
}
const good = { aud: [AUD], iss: `https://${TEAM}`, email: OWNER, exp: Math.floor(Date.now() / 1000) + 3600 }
const owner = await token(good)

const inst = (state) => `<reservationSet><item><instancesSet><item><instanceId>i-0b0d</instanceId><instanceState><code>80</code><name>${state}</name></instanceState><launchTime>2026-11-13T10:00:00.000Z</launchTime></item></instancesSet></item></reservationSet>`
let calls
const stub = ({ state = "stopped", refuse = null, origin = 200 } = {}) => async (input) => {
  const u = typeof input === "string" ? input : input.url
  calls.push(u)
  if (u.includes("/cdn-cgi/access/certs")) return Response.json({ keys: [jwk] })
  if (u.includes("amazonaws.com")) {
    if (u.includes("Action=DescribeInstances")) return new Response(inst(state))
    if (refuse && (u.includes("Action=StartInstances") || u.includes("Action=CreateTags"))) return new Response(refuse, { status: 403 })
    return new Response("<ok/>")
  }
  if (u.startsWith(`https://${HOST}/`)) return new Response("<title>Place studio</title>", { status: origin })
  throw new Error("unexpected fetch " + u)
}
const env = () => ({ AWS_KEY_ID: "k", AWS_SECRET: "s", DOMAIN: "example.com", STUDIO_HOST: HOST, ACCESS_TEAM: TEAM, STUDIO_AUD: AUD, OWNER_EMAIL: OWNER })
const open = (tok, path = "/") => worker.fetch(new Request(`https://${HOST}${path}`, { headers: tok ? { "cf-access-jwt-assertion": tok } : {} }), env())
const started = () => calls.some((u) => u.includes("Action=StartInstances"))
let n = 0

// 1. the owner, the machine stopped: tagged first, then started; the waiting page reloads into the studio
calls = []; globalThis.fetch = stub()
let r = await open(owner), body = await r.text()
assert.equal(r.status, 503); assert.match(body, /<h1>Starting the build machine<\/h1>/); assert.match(body, /This takes about a minute/)
assert.match(body, /http-equiv="refresh"/, "the page reloads by itself"); assert.doesNotMatch(body, /Stop the game machine/)
const tag = calls.findIndex((u) => u.includes("Action=CreateTags")), start = calls.findIndex((u) => u.includes("Action=StartInstances"))
assert.ok(tag >= 0 && start > tag, "the studio-start tag is written before the start")
assert.ok(calls[tag].includes(`Tag.1.Key=${STUDIO_START_TAG}`) && calls[tag].includes("ResourceId.1=i-0b0d"))
assert.ok(calls.some((u) => u.includes("ec2.eu-west-2.amazonaws.com")), "the build machine's region"); n += 6

// the Access cookie serves as well as the header
calls = []; globalThis.fetch = stub()
r = await worker.fetch(new Request(`https://${HOST}/`, { headers: { cookie: `CF_Authorization=${owner}` } }), env())
assert.match(await r.text(), /Starting the build machine/); assert.ok(started()); n += 2

// 2. the owner, the machine up: the request goes on to the tunnel unchanged, nothing started
calls = []; globalThis.fetch = stub({ state: "running" })
r = await open(owner); body = await r.text()
assert.equal(r.status, 200); assert.match(body, /Place studio/); assert.equal(r.headers.get("x-argonia-switch"), "studio")
assert.ok(!started() && !calls.some((u) => u.includes("CreateTags"))); n += 4
// up but the studio not answering yet: a waiting page, nothing started
calls = []; globalThis.fetch = stub({ state: "running", origin: 530 })
r = await open(owner); assert.match(await r.text(), /the studio is starting/); assert.ok(!started()); n += 2

// 3. not the owner: refused, nothing started
for (const [why, tok] of [["no sign-in", null], ["another email", await token({ ...good, email: "someone@example.com" })],
                          ["another app", await token({ ...good, aud: ["other"] })], ["expired", await token({ ...good, exp: 1 })],
                          ["a forged signature", await token(good, "k1", (await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign"])).privateKey)],
                          ["an unknown key", await token(good, "k9")]]) {
  calls = []; globalThis.fetch = stub()
  r = await open(tok)
  assert.equal(r.status, 403, why); assert.match(await r.text(), /Only the owner can start the build machine/, why)
  assert.ok(!started() && !calls.some((u) => u.includes("CreateTags")), why + ": nothing started"); n += 3
}
calls = []; globalThis.fetch = stub({ state: "running" })
assert.equal((await open(null, "/argonia/status")).status, 403, "the status is the owner's"); n += 1
assert.equal(await isOwner(new Request(`https://${HOST}/`, { headers: { "cf-access-jwt-assertion": owner } }), { ...env(), OWNER_EMAIL: "" }), false, "not configured: no one"); n += 1

// 4. AWS refuses the start: a plain message with what to do, no reload loop
calls = []; globalThis.fetch = stub({ refuse: "<Response><Errors><Error><Code>UnauthorizedOperation</Code><Message>You are not authorized</Message></Error></Errors></Response>" })
r = await open(owner); body = await r.text()
assert.match(body, /<h1>The build machine could not start<\/h1>/); assert.match(body, /AWS said: [^<]*UnauthorizedOperation/)
assert.match(body, /Try again in a few minutes/); assert.match(body, /AWS console/); assert.doesNotMatch(body, /http-equiv="refresh"/); n += 5
// still settling after a stop: "Starting…" and it tries again at each reload
calls = []; globalThis.fetch = stub({ refuse: "<Code>IncorrectInstanceState</Code>" })
r = await open(owner); assert.match(await r.text(), /<h1>Starting…<\/h1>/); n += 1

// the play machine's page is unchanged by the studio's host
calls = []; globalThis.fetch = stub()
r = await worker.fetch(new Request("https://play.example.com/"), env())
assert.match(await r.text(), /Starting Paris/); assert.ok(calls.some((u) => u.includes("ec2.eu-west-3.amazonaws.com"))); n += 2
console.log(`studio address: ${n} checks pass`)

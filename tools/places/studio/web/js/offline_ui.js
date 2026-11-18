// What the owner sees of offline working (docs/design/place-studio.md, Offline): the Offline panel (take a place
// offline, update or remove it, the places held, sending), the one calm line under the top bar, the wake, and the
// choice when a save moved on while he was away. The store and the send are offline.js.
import { off, mb, Unavailable } from './offline.js';

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const when = (t) => (t ? new Date(t).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'unknown');
const ago = (t) => { const d = (Date.now() - new Date(t).getTime()) / 3600e3; return d < 1 ? 'under an hour ago' : d < 48 ? `${Math.round(d)} hours ago` : `${Math.round(d / 24)} days ago`; };
const secs = (s) => (s < 90 ? `${Math.round(s)} seconds` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`);
const changes = (n) => `${n} change${n === 1 ? '' : 's'}`;

export const STEPS = [
  'While online, open the place and choose "Use this place offline" in this panel. Wait until it says the place is held.',
  'Work anywhere: with no connection, or with the build machine stopped, open the studio as usual. It opens from this tablet and says it is offline.',
  'Edit, write notes and save as always. Everything is kept on this tablet, even if you close the browser or restart the tablet.',
  'When you are back online, press "Start the build machine" if it is stopped, and wait for "The build machine is back".',
  'Choose "Send my offline work", or "Send it, then save and finalise". Nothing is sent until you choose; if a save changed meanwhile you are asked which to keep.',
];

export class OfflineUI {
  constructor(app) {
    this.app = app; this.back = false; this.unsentN = 0; this.busy = null;
    $('#offline-btn')?.addEventListener('click', () => this.panel());
    off.on(() => this.render());
    navigator.serviceWorker?.addEventListener?.('message', (e) => { if (e.data?.type === 'fell-back' && !off.active) this.lost(); });
    addEventListener('online', () => this.check());
    this.timer = setInterval(() => { if (off.active && !this.back) this.check(); }, 30000);
  }
  // The connection went while a held place was open: from here every write stays on this tablet.
  async lost() {
    if (off.active || !this.app.place || !(await off.heldFor(this.app.place.place_id))) return;
    await off.setMode(true, 'down'); this.app.toast('The build machine cannot be reached: you are working offline. Your changes are kept on this tablet.', 7000);
  }
  async check() {
    // one probe at a time, and no more than one every five seconds (the browser's online events can come in bursts)
    if (this.checking) return this.checking;
    if (Date.now() - (this.checkedAt || 0) < 5000) return this.lastCheck;
    this.checking = this.probeOnce().finally(() => { this.checking = null; this.checkedAt = Date.now(); });
    return this.checking;
  }
  async probeOnce() {
    const p = await off.probe();
    this.lastCheck = p.state;
    if (p.state === 'online') { off.status = p.status; if (off.active) { this.back = true; this.render(); } }
    else if (off.active) { this.back = false; off.why = p.state === 'net' ? 'net' : p.state === 'signed-out' ? 'signed-out' : 'down'; this.render(); }
    return p.state;
  }
  async render() {
    const line = $('#offline-line'); if (!line) return;
    const pid = this.app.place?.place_id, u = pid ? await off.unsent(pid).catch(() => ({ n: 0 })) : { n: 0 };
    this.unsentN = u.n;
    $('#offline-btn')?.setAttribute('data-state', off.active ? 'offline' : u.n ? 'unsent' : 'online');
    let text = '', btn = null;
    if (off.active && this.back) { text = 'The build machine is back. Nothing has been sent yet.'; btn = ['Send my offline work', () => this.panel(true)]; }
    else if (off.active && off.why === 'signed-out') { text = 'Offline: working from this tablet. Your sign-in has run out.'; btn = ['Sign in again to send', () => this.signIn()]; }
    else if (off.active && off.why === 'down') { text = 'Offline: working from this tablet; the build machine is not running.'; btn = ['Start the build machine', () => this.wake()]; }
    else if (off.active) text = 'Offline: working from this tablet. Your changes are kept here until you send them.';
    else if (u.n) { text = `This tablet holds work made offline that is not sent yet (${u.n} item${u.n === 1 ? '' : 's'}).`; btn = ['Send it', () => this.panel(true)]; }
    if (this.busy) text = this.busy;
    line.hidden = !text; line.replaceChildren(el(`<span>${esc(text)}</span>`));
    if (btn && !this.busy) { const b = el(`<button class="quiet">${esc(btn[0])}</button>`); b.onclick = btn[1]; line.append(b); }
    if (this.app.panels.name === 'offline') this.panel(false, true);
  }
  // Ask the play switch to start the build machine (the studio's own address starts it for the owner), then wait.
  async wake() {
    this.busy = 'Asking for the build machine…'; this.render();
    let r = null; try { r = await fetch(`/?wake=${Date.now()}`, { credentials: 'same-origin', cache: 'no-store', redirect: 'manual' }); } catch { r = null; }
    if (!r) { this.busy = null; off.why = 'net'; this.render(); this.app.toast('There is no connection, so the build machine cannot be started from here.', 6000); return; }
    if (r.type === 'opaqueredirect' || r.status === 401 || r.status === 403) { this.busy = null; off.why = 'signed-out'; this.render(); return; }
    this.busy = 'Starting the build machine: this takes about a minute. You can keep working.'; this.render();
    const t0 = Date.now();
    const poll = async () => {
      const s = await this.check();
      if (s === 'online' || Date.now() - t0 > 240000) { this.busy = null; this.render(); if (s !== 'online') this.app.toast('The build machine has not answered yet. Try "Start the build machine" again in a minute.', 7000); return; }
      setTimeout(poll, 5000);
    };
    setTimeout(poll, 5000);
  }
  // A sign-in that ran out: the latest work is kept on this tablet first, then the sign-in page.
  async signIn() {
    try { await this.app.autosave(); } catch { /* kept already, or nothing to keep */ }
    location.href = `${location.origin}/?signin=${Date.now()}`;
  }

  // ---------- the panel ----------
  async panel(sending = false, quiet = false) {
    const a = this.app, P = a.panels, pid = a.place?.place_id; if (!pid) return;
    if (!quiet) P.name = 'offline';
    const parts = [], h = await off.heldFor(pid), all = await off.heldList(), u = await off.unsent(pid);
    if (off.active) parts.push(el(`<p class="tag">${esc(this.back ? 'The build machine can be reached again. Nothing has been sent yet: choose below.' : 'You are working offline. Everything you change is kept on this tablet.')}</p>`));
    // this place
    parts.push(el(`<h3>${esc(a.place.title || pid)} on this tablet</h3>`));
    const prog = el('<div class="offline-progress" hidden><b><i></i></b><span></span></div>');
    if (this.prog) { prog.hidden = false; prog.querySelector('i').style.width = `${this.prog.pct}%`; prog.querySelector('span').textContent = this.prog.text; }
    if (h) {
      const older = !off.active && off.status && a.place.stamps?.draft?.key && h.stamps?.draft && h.stamps.draft !== a.place.stamps.draft.key;
      parts.push(el(`<p>Held offline: ${esc(mb(h.bytes))}, ${h.files} files, taken ${esc(when(h.at))} (${esc(ago(h.at))}).${h.persisted ? '' : ' The browser has not promised to keep it if the tablet runs short of space.'}</p>`));
      if (older) parts.push(el(`<p class="tag nordic">${u.n ? 'Edited offline on an older draft: the place has been redrafted since. Your offline work is kept and sent as it is; when it opens, edits that no longer fit the new draft are shown and not applied.' : 'The place has changed since it was taken offline. Update it before you next work offline.'}</p>`));
    } else parts.push(el('<p>This place is not held on this tablet. Take it offline to work on it with no connection: everything it needs is downloaded to the tablet.</p>'));
    const row = el('<div class="row"></div>');
    if (!off.active) {
      const take = el(`<button class="primary offline-take">${h ? 'Update' : 'Use this place offline'}</button>`);
      take.onclick = () => this.take(a.place, take); row.append(take);
    }
    if (h) { const rm = el('<button class="quiet offline-remove">Remove from this tablet</button>'); rm.onclick = () => this.remove(pid, rm, u.n); row.append(rm); }
    parts.push(row, prog);
    // the work not sent yet
    if (u.n) {
      parts.push(el('<h3>Work made offline, not sent yet</h3>'));
      const lines = [...u.saves.map((s) => `${s.save_id === 'autosave' ? 'Your latest work' : `"${s.body.name || s.save_id}"`}: ${changes((s.body.ops || []).length)}, last changed ${when(s.at)}`),
        ...(u.notes.length ? [`${u.notes.length} note${u.notes.length === 1 ? '' : 's'} for the agent (they arrive unsent: send them to the agent when you choose)`] : []),
        ...(u.changes.length ? [`${u.changes.length} change${u.changes.length === 1 ? '' : 's'} to what a story needs`] : [])];
      parts.push(el(`<ul>${lines.map((l) => `<li>${esc(l)}</li>`).join('')}</ul>`));
      const can = !off.active || this.back;
      const send = el('<button class="primary offline-send">Send my offline work</button>'), fin = el('<button class="quiet offline-send-finalise">Send it, then save and finalise</button>');
      send.disabled = fin.disabled = !can;
      send.onclick = () => this.send(false); fin.onclick = () => this.send(true);
      const r2 = el('<div class="row"></div>'); r2.append(send, fin); parts.push(r2);
      if (!can) parts.push(el('<p class="tag">Sending needs the build machine. It stays on this tablet until you send it.</p>'));
      if (sending && can && !quiet) setTimeout(() => send.focus(), 0);
    }
    // every place held
    if (all.length) {
      parts.push(el('<h3>Places held on this tablet</h3>'));
      const ol = el('<ol class="history offline-held"></ol>');
      for (const x of all) {
        const li = el(`<li><span class="what">${esc(x.title || x.place_id)}<span class="note">${esc(mb(x.bytes))}, taken ${esc(ago(x.at))}</span></span></li>`);
        const r3 = el('<div class="row"></div>');
        if (!off.active) { const up = el('<button class="quiet">Update</button>'); up.onclick = () => this.take(x.place, up); r3.append(up); }
        const rm = el('<button class="quiet">Remove</button>'); rm.onclick = async () => this.remove(x.place_id, rm, (await off.unsent(x.place_id)).n); r3.append(rm);
        li.querySelector('.what').append(r3); ol.append(li);
      }
      parts.push(ol);
    }
    parts.push(el('<h3>How to work offline</h3>'), el(`<ol>${STEPS.map((s) => `<li>${esc(s)}</li>`).join('')}</ol>`));
    parts.push(el(`<p class="tag">Offline, these need the build machine and wait until you are back: finalising, sending notes to the agent, searching beyond what this tablet holds (the search looks only in the source place and our place), a model that was never downloaded (it shows as a box), the world map, and following a finalise.</p>`));
    if (P.name === 'offline') P.show('Offline', parts);
  }
  // The progress is kept here and drawn by the panel, so a panel drawn again meanwhile shows it too.
  setProg(text, pct) {
    this.prog = { text, pct };
    const p = $('#panel-body .offline-progress');
    if (p) { p.hidden = false; p.querySelector('span').textContent = text; p.querySelector('i').style.width = `${pct}%`; }
  }
  async take(place, btn) {
    const a = this.app; btn.disabled = true;
    try {
      const rec = await off.download(place, (p) => {
        if (p.phase === 'list') { this.setProg('Preparing the list of what the place needs (the build machine converts what it has not yet; this can take a minute).', 0); return; }
        this.setProg(`Downloading: ${p.done} of ${p.of} files, ${mb(p.bytes)} of about ${mb(p.total)}.`, (100 * p.done) / Math.max(1, p.of));
      });
      this.setProg(`Held offline: ${mb(rec.bytes)}, ${rec.files} files, finished at ${when(rec.at)} (took ${secs(rec.seconds)}).${rec.persisted ? '' : ' The browser did not promise to keep it: it may clear it if the tablet runs short of space, so update it before you go offline.'}`, 100);
      a.toast(`${rec.title} is held on this tablet (${mb(rec.bytes)}).`, 6000);
    } catch (e) {
      this.setProg(e instanceof Unavailable ? e.message : `The place was not taken offline: ${e.message}. Nothing on the tablet changed; try again.`, 0);
    }
    btn.disabled = false;
    await this.panel();
  }
  async remove(pid, btn, unsentN) {
    if (btn.dataset.sure !== '1') {
      btn.dataset.sure = '1'; btn.textContent = 'Tap again to remove';
      if (unsentN) this.app.toast('Work not sent yet stays on this tablet when the place is removed, and can still be sent.', 6000);
      return;
    }
    await off.remove(pid); this.panel();
  }

  // ---------- sending ----------
  async send(finalise) {
    const a = this.app, pid = a.place.place_id;
    this.busy = 'Sending your offline work…'; this.render();
    const res = await off.send(pid, { decide: (c) => this.decide(c), progress: (t) => { this.busy = `${t}…`; this.render(); } });
    this.busy = null;
    for (const s of res.saved) a.revs[s.save_id] = s.rev;
    if (!res.stopped && !res.left) { this.back = false; await off.setMode(false); }
    const said = [res.saved.length && `${res.saved.length} save${res.saved.length === 1 ? '' : 's'} stored`,
      res.kept.length && `${res.kept.length} kept as new save${res.kept.length === 1 ? '' : 's'} (${res.kept.map((k) => `"${k.name}"`).join(', ')})`,
      res.dropped.length && `${res.dropped.length} of yours dropped`, res.notes && `${res.notes} note${res.notes === 1 ? '' : 's'} added, unsent`,
      res.changes && `${res.changes} story change${res.changes === 1 ? '' : 's'} recorded`].filter(Boolean).join('; ');
    if (res.signin) off.why = 'signed-out';
    a.toast(res.stopped ? `${said ? said + '. ' : ''}${res.stopped}` : `Sent: ${said || 'nothing was waiting'}.${res.left ? ` ${res.left} item${res.left === 1 ? '' : 's'} left on this tablet.` : ''}`, 9000);
    this.render(); this.panel();
    if (finalise && !res.stopped && !res.left) a.panels.finalise();
  }
  // A save moved on at the server while the owner was offline: both shown in plain words; his is never written over.
  decide({ save, current }) {
    return new Promise(async (done) => {
      let theirs = null; try { const r = await fetch(`/api/place/${save.place_id}/saves/${encodeURIComponent(save.save_id)}`, { credentials: 'same-origin', cache: 'no-store' }); if (r.ok) theirs = await r.json(); } catch { theirs = null; }
      const name = save.save_id === 'autosave' ? 'Your latest work' : `"${save.body.name || save.save_id}"`;
      const o = $('#offline-sheet'); o.hidden = false;
      o.innerHTML = `<div class="sheet" role="dialog" aria-label="A save changed while you were offline"><h2>${esc(name)} changed while you were offline</h2>
        <p>On the build machine it was saved ${esc(when(current.at || theirs?.at))}${theirs ? `, with ${esc(changes((theirs.ops || []).length))}` : ''}${current.final ? ', and it has been finalised' : ''}.</p>
        <p>On this tablet you have ${esc(changes((save.body.ops || []).length))}, last changed ${esc(when(save.at))}.</p>
        <p>Nothing has been overwritten. Keep yours as a new named save beside it, or drop yours.</p>
        <div class="row"><button class="primary keep">Keep mine as a new save</button><button class="danger drop">Drop mine</button><button class="quiet later">Decide later</button></div></div>`;
      const close = (v) => { o.hidden = true; o.innerHTML = ''; done(v); };
      o.querySelector('.keep').onclick = () => close('keep');
      o.querySelector('.later').onclick = () => close('later');
      const drop = o.querySelector('.drop');
      drop.onclick = () => { if (drop.dataset.sure !== '1') { drop.dataset.sure = '1'; drop.textContent = 'Tap again to drop it for good'; return; } close('drop'); };
    });
  }
  // Offline, "Save and finalise" explains instead of failing.
  finaliseOffline() {
    this.app.toast('Finalising needs the build machine. Your work is kept on this tablet; when you are back online, choose "Send it, then save and finalise" here.', 8000);
    this.panel();
  }
}

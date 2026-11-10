// The note bar: a slim strip under the views, always there while editing. It counts the changes since the last
// note, lets the count be trimmed to the last few, marks them fault or taste, and takes one note for all of them
// (typed, handwritten or spoken: it is an ordinary text field). Confirming starts a new group; nothing is modal and
// nothing has to be put away. The words go into the save with the changes they are about (note_groups.js).
import { pending } from './note_groups.js';

const $ = (s) => document.querySelector(s);
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;

export class NoteBar {
  constructor(app) {
    this.app = app; this.take = null; this.el = $('#notebar');
    this.el.innerHTML = `
      <button class="nb-count quiet" aria-label="Show the things these changes touched"></button>
      <span class="nb-step" role="group" aria-label="How many of the latest changes the note is about">
        <button class="nb-less" aria-label="One change fewer">−</button><button class="nb-more" aria-label="One change more">+</button></span>
      <button class="call nb-call" aria-label="Fault or taste: tap to change"></button>
      <input class="nb-text" type="text" enterkeyhint="done" autocomplete="off" aria-label="Note for the agent about these changes">
      <button class="nb-go primary" aria-label="Keep the note with these changes">Note</button>`;
    this.count = this.el.querySelector('.nb-count'); this.call = this.el.querySelector('.nb-call');
    this.text = this.el.querySelector('.nb-text'); this.go = this.el.querySelector('.nb-go');
    this.less = this.el.querySelector('.nb-less'); this.more = this.el.querySelector('.nb-more');
    this.less.onclick = () => { this.take = Math.max(1, this.n() - 1); this.render(); };
    this.more.onclick = () => { this.take = Math.min(this.pending().length, this.n() + 1); this.render(); };
    this.call.onclick = () => {
      const ops = this.ops(); if (!ops.length) return;
      this.app.log.setCall(ops.map((o) => o.n), this.callOf(ops) === 'taste' ? 'fault' : 'taste');
    };
    this.go.onclick = () => this.confirm();
    this.text.onkeydown = (e) => { if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); this.confirm(); } };
    this.text.oninput = () => this.render();
    this.count.onclick = () => this.app.panels.selectTouched(this.ops());
  }
  pending() { return this.app.log ? pending(this.app.log.applied()) : []; }
  n() { const p = this.pending().length; return Math.min(this.take ?? p, p); }
  // The ops of the changes the note will cover: the last n of those since the last note.
  ops() { const p = this.pending(), n = this.n(); return n ? p.slice(p.length - n).flat() : []; }
  callOf(ops) { return ops.length && ops.every((o) => o.call === 'taste') ? 'taste' : 'fault'; }
  // Called after every change, undo, redo, call or note.
  changed(kind) {
    if (kind === 'push' || kind === 'load') this.take = null;
    this.render();
  }
  render() {
    if (!this.app.log) { this.el.hidden = true; return; }
    this.el.hidden = false;
    const p = this.pending().length, n = this.n(), ops = this.ops(), call = this.callOf(ops);
    this.count.textContent = !p ? 'No changes since your last note' : n === p ? `${plural(p, 'change')} since your last note`
      : `The last ${plural(n, 'change')} of ${p} since your last note`;
    this.count.disabled = !p; this.el.dataset.count = String(n);
    this.less.disabled = n <= 1; this.more.disabled = n >= p;
    this.call.dataset.call = call; this.call.textContent = call === 'taste' ? 'Taste' : 'Fault'; this.call.disabled = !p;
    this.text.placeholder = p ? `Say what was wrong, for the agent (${n === 1 ? 'this change' : `these ${n} changes`})` : 'Change something, then say here what was wrong';
    this.go.disabled = !p || !this.text.value.trim();
  }
  confirm() {
    const ops = this.ops(), n = this.n(), words = this.text.value.trim();
    if (!ops.length || !words) return;
    this.app.log.setNote(ops.map((o) => o.n), words, this.callOf(ops));
    this.text.value = ''; this.take = null;
    this.app.toast(`Note kept with ${n === 1 ? 'that change' : `those ${n} changes`}.`);
    this.render();
  }
}

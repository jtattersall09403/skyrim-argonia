// The Atlas (the world map page, built by `python3 -m tools.newworld.map_page` and served by the studio at
// /atlas/) shown over the studio on request, opened on the place being edited (#place=<id>). Nothing of the
// Atlas is copied here: the frame loads the built page itself, the first time the map is opened.
const ATLAS = `${window.STUDIO_API || ''}/atlas/index.html`;
export function setupAtlas({ placeId, toast }) {
  const btn = document.getElementById('atlas-btn'), box = document.getElementById('atlas'), frame = box.querySelector('iframe');
  let built = null; // null: not yet asked; true or false once the server has answered
  const ask = () => fetch(ATLAS, { method: 'HEAD', credentials: 'same-origin' }).then((r) => r.ok).catch(() => false)
    .then((ok) => {
      built = ok; btn.dataset.built = ok ? '1' : '0';
      btn.title = ok ? 'See where this place is in the wider world' : 'The world map has not been built on this machine yet';
      btn.querySelector('span').textContent = ok ? 'World map' : 'World map (not built)';
      return ok;
    });
  ask();
  const close = () => { box.hidden = true; btn.setAttribute('aria-expanded', 'false'); btn.focus(); };
  btn.onclick = async () => {
    if (!(built ?? await ask())) { toast('The world map has not been built on this machine yet, so it cannot be shown.', 6000); return; }
    const src = `${ATLAS}#place=${encodeURIComponent(placeId() || '')}`;
    if (frame.dataset.src !== src) { frame.dataset.src = src; frame.src = src; }
    box.hidden = false; btn.setAttribute('aria-expanded', 'true'); box.querySelector('#atlas-close').focus();
  };
  box.querySelector('#atlas-close').onclick = close;
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !box.hidden) close(); });
}

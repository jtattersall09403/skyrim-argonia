// The type scale follows the viewport, so the same view reads on a 1080p desktop, a 720p window and the Magic V5
// streamed at 1:1 (0.2 §d records no stream scale, so 1:1; folded 2376x1060 at 404 ppi, unfolded 2352x2172 at
// 403 ppi). 1rem = min(height / 34, width / 52), and height / 26 on a screen 2:1 or wider, which is a phone held
// landscape (the fold closed is 2.24:1; a desktop is 16:9 or 16:10): 31.8 px at 1920x1080, 21.2 px at 1280x720,
// 40.8 px folded (2.56 mm), 45.2 px unfolded (2.85 mm). No text in our views is set below 1rem (ui/DESIGN.md; the
// harness measures it in every still).
export const PHONE_ASPECT = 2;
export const remFor = (w: number, h: number): number => Math.min(h / (w / h >= PHONE_ASPECT ? 26 : 34), w / 52);

export function installScale(): void {
  const set = () => {
    document.documentElement.style.fontSize = `${remFor(window.innerWidth, window.innerHeight).toFixed(2)}px`;
  };
  set();
  window.addEventListener("resize", set);
}

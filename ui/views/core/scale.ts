// The type scale follows the viewport, so the same view reads on a 1080p desktop, a 720p window and the Magic V5
// streamed at 1:1 (0.2 §d records no stream scale, so 1:1; folded 2376x1060 at 404 ppi, unfolded 2352x2172 at
// 403 ppi). 1rem = min(height / 34, width / 52): 31.8 px at 1920x1080, 21.2 px at 1280x720, 31.2 px folded (1.96 mm),
// 45.2 px unfolded (2.85 mm). No text in our views is set below 1rem (ui/DESIGN.md, the harness measures it).
export const remFor = (w: number, h: number): number => Math.min(h / 34, w / 52);

export function installScale(): void {
  const set = () => {
    document.documentElement.style.fontSize = `${remFor(window.innerWidth, window.innerHeight).toFixed(2)}px`;
  };
  set();
  window.addEventListener("resize", set);
}

// The type scale follows the viewport, so the same view reads on a 1080p desktop, a 720p window and the Magic V5
// streamed at 1:1 (0.2 §d records no stream scale, so 1:1; folded 2376x1060 at 404 ppi, unfolded 2352x2172 at
// 403 ppi). 1rem = min(height / 34, width / 52), and height / 26 on a screen 2:1 or wider, which is a phone held
// landscape (the fold closed is 2.24:1; a desktop is 16:9 or 16:10): 31.8 px at 1920x1080, 21.2 px at 1280x720,
// 40.8 px folded (2.56 mm), 45.2 px unfolded (2.85 mm). No text in our views is set below 1rem (ui/DESIGN.md; the
// harness measures it in every still).
// The phone's scale is for a phone, so it keys on the device: aspect 2:1 or wider AND a small screen, measured in
// device pixels (css px x density). A 21:9 monitor (2560x1080, 3440x1440, a 5120x2160 retina) is wider than 2440
// device px and keeps the desktop scale; the fold (2376 wide) and a smaller 2:1 window stay on the phone's.
export const PHONE_ASPECT = 2;
export const PHONE_MAX_DEVICE_W = 2440;
export const isPhoneLandscape = (w: number, h: number, dpr = 1): boolean => w / h >= PHONE_ASPECT && w * dpr <= PHONE_MAX_DEVICE_W;
export const remFor = (w: number, h: number, dpr = 1): number => Math.min(h / (isPhoneLandscape(w, h, dpr) ? 26 : 34), w / 52);

export function installScale(): void {
  const set = () => {
    document.documentElement.style.fontSize = `${remFor(window.innerWidth, window.innerHeight, window.devicePixelRatio || 1).toFixed(2)}px`;
  };
  set();
  window.addEventListener("resize", set);
}

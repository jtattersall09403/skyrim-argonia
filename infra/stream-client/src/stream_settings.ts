// Stream settings chosen for the device before upstream reads them (chunk 0.0 §c, owner 2026-10-29):
// - the stream is the size of this whole screen in real pixels (upstream goes full screen on the first tap), so the unfolded Magic V5, the folded phone, the Mac, a
//   monitor or a tablet each fill the screen (the host matches its desktop to the request, sunshine-prep.ps1);
// - the bitrate follows the pixel count;
// - pads keep the Xbox layout: upstream names the Gamepad API's bottom button (0) "b" and the left one (2) "y", the
//   Nintendo layout, so on the GameSir X2s and the touch pad A acted as B and X as Y in Skyrim (measured with
//   XInput on the game machine, 2026-10-29); its invertAB and invertXY put them back;
// - the mouse is relative (games turn the camera by movement; upstream's "follow" sends absolute positions, which
//   pins Skyrim's camera), and the pointer is captured on the first click in the stream (Escape releases it).

export const MAX_EDGE = 2560   // the T4's NVENC and the stream budget: larger screens are scaled to fit
export const MAX_HEIGHT = 2160 // taller streams never start (2352 x 2172, the unfolded Magic V5 in full screen,
                               // failed to connect; 2352 x 2160 streams, measured 2026-10-29)
export const MIN_KBPS = 8000
export const MAX_KBPS = 50000

/** The stream size for a screen: its physical pixels, longest edge within MAX_EDGE and height within MAX_HEIGHT,
 *  both sides even. */
export function streamSize(cssW: number, cssH: number, dpr: number): { width: number, height: number } {
    let w = cssW * dpr, h = cssH * dpr
    const k = Math.min(1, MAX_EDGE / Math.max(w, h), MAX_HEIGHT / h)
    w *= k; h *= k
    const even = (n: number) => Math.max(2, Math.round(n / 2) * 2)
    return { width: even(w), height: even(h) }
}

/** Bitrate for a size at 60 fps: about 0.2 bits a pixel a frame (0.1 looked soft to the owner), inside [MIN_KBPS, MAX_KBPS]. */
export function bitrateFor(width: number, height: number): number {
    return Math.round(Math.min(MAX_KBPS, Math.max(MIN_KBPS, (width * height * 60 * 0.2) / 1000)))
}

/** The whole screen in CSS pixels, in its current orientation. Upstream goes full screen on the first tap or click,
 *  so the stream is sized to the screen, not to the page before full screen (the browser's bars left a black strip
 *  along the bottom of the unfolded Magic V5 in landscape, owner 2026-10-29). */
export function fullScreenCss(scr: { width: number, height: number } = screen,
    landscape = window.matchMedia?.("(orientation: landscape)").matches): { width: number, height: number } {
    let { width, height } = scr
    if (!width || !height) return { width: window.innerWidth, height: window.innerHeight }
    if (landscape !== undefined && landscape !== width >= height) [width, height] = [height, width]
    return { width, height }
}

export function applyStreamSettings(storage: Storage = localStorage) {
    const scr = fullScreenCss()
    const size = streamSize(scr.width, scr.height, window.devicePixelRatio || 1)
    let s: Record<string, unknown> = {}
    try { s = JSON.parse(storage.getItem("mlSettings") ?? "{}") ?? {} } catch { s = {} }
    Object.assign(s, {
        videoSize: "custom",
        videoSizeCustom: size,
        bitrate: bitrateFor(size.width, size.height),
        fps: 60,
        mouseMode: "relative",
        controllerConfig: { ...(s.controllerConfig as object ?? {}), invertAB: true, invertXY: true },
    })
    try { storage.setItem("mlSettings", JSON.stringify(s)) } catch { /* private mode: upstream defaults */ }
    return size
}

/** Capture the pointer on the first click in the stream on a mouse device (relative mouse needs it). */
export function capturePointerOnClick() {
    document.addEventListener("mousedown", (e) => {
        if (document.pointerLockElement) return
        const t = e.target as Element | null
        if (!t || t.closest("#sidebar-root, #argonia-touch, #argonia-touch-toggle, #argonia-keyboard-toggle, button, input, select, textarea")) return
        const v = document.querySelector<HTMLElement>("video.video-stream, #root canvas") ?? document.body
        try { void v.requestPointerLock?.() } catch { /* not allowed here */ }
    }, { capture: true })
}

"""A DDS (BC1, BC3, BC5, BC7, uncompressed; mipmapped or not) to WebP no larger than a requested size, alpha kept on diffuse textures.

Pillow decodes the top mip level; the image is reduced by halving (box filter, the way a mip chain is made) to the
largest power-of-two step not over `size` on its longer side. A normal map (BC5 two-channel) gets its blue channel
rebuilt so it reads as a normal map. Lossy WebP at quality 82 with alpha; a texture with no alpha below 255 is
written without an alpha channel."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

SIZES = (64, 128, 256, 512, 1024, 2048)
QUALITY = 82


def clamp_size(size: int) -> int:
    return min((s for s in SIZES if s >= int(size)), default=SIZES[-1])


def decode(dds: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(dds))
    im.load()
    if im.mode in ("LA", "La"):
        im = im.convert("RGBA")
    if im.mode == "RGB" and _is_bc5(dds):
        a = np.asarray(im).astype(np.float32) / 127.5 - 1.0
        z = np.sqrt(np.clip(1.0 - a[..., 0] ** 2 - a[..., 1] ** 2, 0, 1))
        a[..., 2] = z
        im = Image.fromarray(((a + 1.0) * 127.5).clip(0, 255).astype(np.uint8), "RGB")
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    return im


def _is_bc5(dds: bytes) -> bool:
    four = dds[84:88]
    if four in (b"ATI2", b"BC5U", b"BC5S"):
        return True
    return four == b"DX10" and len(dds) > 128 and int.from_bytes(dds[128:132], "little") in (82, 83, 84)


def to_webp(dds: bytes, size: int, keep_alpha: bool = True) -> tuple[bytes, dict]:
    """keep_alpha False for normal maps and land textures, whose alpha is specular, not cut-out."""
    im = decode(dds)
    w, h = im.size
    limit = clamp_size(size)
    while max(w, h) > limit and min(w, h) > 1:
        w, h = max(1, w // 2), max(1, h // 2)
    if (w, h) != im.size:
        im = im.resize((w, h), Image.Resampling.BOX)
    has_alpha = keep_alpha and im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 255
    if im.mode == "RGBA" and not has_alpha:
        im = im.convert("RGB")
    out = io.BytesIO()
    im.save(out, "WEBP", quality=QUALITY, method=4)
    rgb = np.asarray(im.convert("RGB").resize((1, 1), Image.Resampling.BOX)).reshape(3)
    return out.getvalue(), {"w": w, "h": h, "alpha": has_alpha, "avg": "#%02x%02x%02x" % tuple(int(x) for x in rgb)}

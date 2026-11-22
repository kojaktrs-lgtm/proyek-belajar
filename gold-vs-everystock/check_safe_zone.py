"""Render frames across the video and report any content inside TikTok/Shorts UI areas.

Also writes output/safezone_mock.png: key frames with the UI areas shaded red.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import make_video as mv

BG = np.array([7, 8, 12])


def unsafe_mask():
    m = np.zeros((mv.H, mv.W), bool)
    m[:, : mv.SAFE_LEFT] = m[:, mv.SAFE_RIGHT:] = True
    m[: mv.SAFE_TOP] = m[mv.SAFE_BOTTOM:] = True
    m[mv.BTN_Y:, mv.BTN_X:] = True
    return m


def main():
    mv.configure(sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL")
    mask = unsafe_mask()
    r = mv.Renderer()
    shots, worst = {}, []
    keep = {int(1.5 * mv.FPS): "countdown", int(9 * mv.FPS): "race", int(23.5 * mv.FPS): "late",
            mv.N_FRAMES - int(mv.LOOP_FADE * mv.FPS) - 1: "finale"}
    for k in range(mv.N_FRAMES):
        img = r.frame(k)
        if k % 10 == 0 or k in keep:
            fg = np.abs(img.astype(int) - BG).sum(axis=2) > 60
            bad = fg & mask
            if bad.any():
                ys, xs = np.where(bad)
                worst.append((k, int(bad.sum()), xs.min(), xs.max(), ys.min(), ys.max()))
        if k in keep:
            shots[keep[k]] = img
    if worst:
        print("CONTENT IN UNSAFE AREAS (frame, pixels, x-range, y-range):")
        for w in worst[:20]:
            print("  ", w)
    else:
        print("OK: no content in TikTok/Shorts UI areas")

    tiles = []
    for name in ("countdown", "race", "late", "finale"):
        im = Image.fromarray(shots[name]).convert("RGBA")
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        red = (255, 40, 40, 70)
        for box in ((0, 0, mv.SAFE_LEFT, mv.H), (mv.SAFE_RIGHT, 0, mv.W, mv.H),
                    (0, 0, mv.W, mv.SAFE_TOP), (0, mv.SAFE_BOTTOM, mv.W, mv.H),
                    (mv.BTN_X, mv.BTN_Y, mv.W, mv.H)):
            d.rectangle(box, fill=red)
        tiles.append(Image.alpha_composite(im, ov).convert("RGB"))
    sheet = Image.new("RGB", (4 * mv.W + 60, mv.H), (40, 40, 40))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (mv.W + 20), 0))
    sheet.resize((sheet.width // 3, sheet.height // 3)).save(mv.OUT_DIR / f"safezone_mock_{mv.TICKER.lower()}.png")


if __name__ == "__main__":
    main()

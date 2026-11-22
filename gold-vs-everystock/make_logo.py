"""Profile logo for the Gold vs Everystock channel.

Two chart lines (gold and white "every stock") start from the same point,
cross each other (the "vs") and race up to arrow tips. No small text, so it
stays readable as a 40 px circle. Everything sits inside the circular crop.

    python make_logo.py   # -> brand/profile_1024.png, profile_800.png, profile_200.png,
                          #    brand/logo_preview.png (circle crops at real app sizes)
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).parent / "brand"
S = 2048                     # draw at 2x, downsample for clean edges
C = S / 2
BG = (7, 8, 12)
GOLD = (247, 197, 72)
STOCK = (223, 228, 238)
GRID = (28, 31, 42)

# chart paths in a 0..1 box (x right, y up); both start at the same point
# Few, bold segments so the mark survives at 40 px; the two lines cross twice (the "vs").
# The arrow tips end apart (gold steep up, stock out to the right) so both read as arrows.
GOLD_PTS = [(0.00, 0.00), (0.30, 0.52), (0.52, 0.30), (0.84, 1.00)]
STOCK_PTS = [(0.00, 0.00), (0.34, 0.18), (0.62, 0.62), (1.00, 0.68)]
BOX = (0.20, 0.23, 0.58, 0.50)      # left, bottom, width, height as a fraction of the canvas


def to_px(pts):
    l, b, w, h = BOX
    return [(S * (l + x * w), S * (1 - (b + y * h))) for x, y in pts]


def arrow_head(p_prev, tip, size):
    ang = math.atan2(tip[1] - p_prev[1], tip[0] - p_prev[0])
    fwd = np.array([math.cos(ang), math.sin(ang)])
    nrm = np.array([-fwd[1], fwd[0]])
    tip = np.array(tip)
    apex = tip + fwd * size * 0.62
    base = tip - fwd * size * 0.38
    return [tuple(apex), tuple(base + nrm * size * 0.5), tuple(base - nrm * size * 0.5)]


def draw_line(layer, pts, col, width, head):
    d = ImageDraw.Draw(layer)
    d.line(pts, fill=col, width=width, joint="curve")
    r = width / 2
    x, y = pts[0]
    d.ellipse((x - r, y - r, x + r, y + r), fill=col)      # round start cap
    d.polygon(arrow_head(pts[-2], pts[-1], head), fill=col)


def glow(pts, col, width, head):
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for blur, alpha, extra in ((70, 90, 30), (28, 140, 10)):
        g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw_line(g, pts, col + (alpha,), width + extra, head + extra)
        out = Image.alpha_composite(out, g.filter(ImageFilter.GaussianBlur(blur)))
    sharp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_line(sharp, pts, col + (255,), width, head)
    return Image.alpha_composite(out, sharp)


def make():
    img = Image.new("RGBA", (S, S), BG + (255,))
    # soft radial lift in the centre so the mark doesn't sit in a flat void
    yy, xx = np.mgrid[0:S, 0:S]
    rr = np.hypot(xx - C, yy - C) / (S / 2)
    lift = np.clip(1 - rr, 0, 1) ** 2 * 14
    base = np.array(BG, float)[None, None, :] + lift[..., None] * np.array([1.0, 1.0, 1.4])
    img = Image.fromarray(np.dstack([base.clip(0, 255).astype(np.uint8), np.full((S, S), 255, np.uint8)]), "RGBA")

    # three faint grid lines, clipped to the circle
    d = ImageDraw.Draw(img)
    for fy in (0.38, 0.62):
        y = S * fy
        half = math.sqrt(max(0.0, (S * 0.40) ** 2 - (y - C) ** 2))
        d.line((C - half, y, C + half, y), fill=GRID + (255,), width=6)

    w, head = 96, 230
    mark = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mark = Image.alpha_composite(mark, glow(to_px(STOCK_PTS), STOCK, w, head))
    mark = Image.alpha_composite(mark, glow(to_px(GOLD_PTS), GOLD, w, head))   # gold on top
    # centre the mark optically: centre of its solid (non-glow) pixels on the canvas centre
    solid = np.asarray(mark)[:, :, 3] > 200
    ys, xs = np.where(solid)
    dx = round(C - (xs.min() + xs.max()) / 2)
    dy = round(C - (ys.min() + ys.max()) / 2)
    shifted = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shifted.paste(mark, (dx, dy), mark)
    img = Image.alpha_composite(img, shifted)
    return img.convert("RGB")


def circle(im, size, ring=None):
    im = im.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


def preview(logo):
    """Circle crops at real app sizes on dark and light app backgrounds."""
    sizes = (400, 160, 96, 56, 40)
    W = sum(sizes) + 60 * (len(sizes) + 1)
    sheet = Image.new("RGB", (W, 2 * 460), (255, 255, 255))
    for row, bg in enumerate(((0, 0, 0), (255, 255, 255))):
        band = Image.new("RGB", (W, 460), bg)
        x = 60
        for s in sizes:
            band.paste(circle(logo, s), (x, (460 - s) // 2), circle(logo, s))
            x += s + 60
        sheet.paste(band, (0, row * 460))
    sheet.save(OUT / "logo_preview.png")


def check_inside_circle(logo):
    """Every bright pixel of the mark must sit inside the circular crop (r = 46%)."""
    a = np.asarray(logo).astype(int)
    bright = np.abs(a - np.array(BG)).sum(axis=2) > 300
    ys, xs = np.where(bright)
    n = logo.size[0]
    r = np.hypot(xs - n / 2, ys - n / 2).max() / n
    cx, cy = (xs.min() + xs.max()) / 2 / n, (ys.min() + ys.max()) / 2 / n
    print(f"mark reaches {r:.1%} from the centre (crop edge 50%); "
          f"bbox centre at ({cx:.3f}, {cy:.3f}) of the canvas; spans {(xs.max()-xs.min())/n:.0%} x {(ys.max()-ys.min())/n:.0%}")


def main():
    OUT.mkdir(exist_ok=True)
    big = make()
    final = big.resize((1024, 1024), Image.LANCZOS)
    for s in (1024, 800, 200):
        final.resize((s, s), Image.LANCZOS).save(OUT / f"profile_{s}.png")
    check_inside_circle(final)
    preview(final)
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()

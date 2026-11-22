"""Render a vertical (1080x1920) line-race short: $1,000 in Gold vs a stock, 10 years.

Usage:
    python make_video.py NKE            # full video -> output/gold_vs_nke.mp4
    python make_video.py NKE --preview  # a few still frames -> output/preview_*.png

Stocks are configured in stocks.py (name, colour, event captions).
"""
import argparse
import math
import subprocess
import wave
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon
from matplotlib.transforms import IdentityTransform
import numpy as np
import pandas as pd

from stocks import STOCKS

HERE = Path(__file__).parent
OUT_DIR = HERE / "output"

# ---------------------------------------------------------------- settings
W, H, FPS = 1080, 1920, 30
# INTRO = 3-2-1 countdown. FINALE ends right as the question finishes appearing,
# so the loop cross-fade starts immediately (no frozen frames at the end).
INTRO, RACE, FINALE, LOOP_FADE = 3.0, 22.0, 3.6, 0.8
TOTAL = INTRO + RACE + FINALE
N_FRAMES = int(round(TOTAL * FPS))

BG = "#07080c"
GRID = "#1c1f2a"
MUTED = "#8a8f9e"
TEXT = "#f2f3f7"
GOLD = "#f7c548"
ACCENT_UP, ACCENT_DOWN = "#3ddc84", "#ff5c5c"

# ---- TikTok / Shorts safe zone (pixels from the TOP-left of the 1080x1920 frame).
# Measured from a real TikTok screenshot: phones taller than 9:16 crop ~52 px per side,
# the search bar covers the top ~225 px, the like/comment column sits at x >= ~900 from
# y ~1050 down, and the caption starts at y ~1630.
SAFE_LEFT, SAFE_RIGHT, SAFE_TOP, SAFE_BOTTOM = 80, 1000, 240, 1600
BTN_X, BTN_Y = 880, 980      # keep x <= BTN_X for anything below y = BTN_Y

# vertical positions (from top)
TITLE_Y, SUB_Y, DATE_Y, PILL_Y = 315, 410, 470, 552
FOOTER_Y = (1536, 1561, 1586)   # small print sits at the very bottom of the safe zone

# axes rectangle in pixels (left, bottom, width, height), origin bottom-left
AX_PX = (100, H - 1500, 770, 1500 - 625)
TIP_FRAC = 0.60          # where the arrow tips sit horizontally inside the axes

TITLE_GAP = 30  # px between title words

# filled in by configure(ticker)
TICKER = NAME = LABEL = STOCK = None
TITLE_PARTS, EVENTS = [], []


def configure(ticker):
    """Select which stock races gold (see stocks.py)."""
    global TICKER, NAME, LABEL, STOCK, TITLE_PARTS, EVENTS
    cfg = STOCKS[ticker]
    TICKER, NAME, LABEL, STOCK = ticker, cfg["name"], cfg["label"], cfg["color"]
    TITLE_PARTS = [("GOLD", GOLD, 80, "heavy"), ("vs", MUTED, 46, "bold"), (NAME, STOCK, 80, "heavy")]
    EVENTS = cfg["events"]


def setup_fonts():
    for f in font_manager.findSystemFonts(["/usr/share/fonts/opentype/inter"]):
        font_manager.fontManager.addfont(f)
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]


# ---------------------------------------------------------------- data
def load_series():
    df = pd.read_csv(HERE / "data" / f"prices_{TICKER}.csv", parse_dates=["date"], index_col="date")
    stock = 1000 * df.stock_adj_close / df.stock_adj_close.iloc[0]
    gold = 1000 * df.gld_close / df.gld_close.iloc[0]
    dates = df.index.values.astype("datetime64[D]").astype(float)  # days since epoch
    return dates, stock.values, gold.values, df.index


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def race_progress(t):
    """0..1 over the race, gentle ease at both ends, near-linear in the middle."""
    x = clamp((t - INTRO) / RACE)
    smooth = 0.5 - 0.5 * math.cos(math.pi * x)
    return 0.65 * x + 0.35 * smooth


# ---------------------------------------------------------------- renderer
class Renderer:
    def __init__(self):
        setup_fonts()
        self.d, self.a, self.g, self.idx = load_series()
        self.n = len(self.d)
        self.y_lo, self.y_hi = 900.0, 1150.0
        self.angle = {"stock": 0.0, "gold": 0.0}
        first, last = self.idx[0], self.idx[-1]
        self.subtitle = f"$1,000 invested in {first:%b %Y}"
        self.footer = (f"Daily closes · {first:%b %-d, %Y} – {last:%b %-d, %Y}",
                       f"Gold = GLD ETF · {LABEL} incl. reinvested dividends",
                       "Past performance ≠ future results · Not financial advice")
        self.events = [(np.datetime64(s).astype(float), np.datetime64(e).astype(float), c)
                       for s, e, c in EVENTS]
        self.fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
        self.measure_title()
        if not COUNT_INK:
            measure_countdown_digits()

    def measure_title(self):
        """Measure each title word so the whole "GOLD vs <STOCK>" line is truly centred."""
        rend = self.fig.canvas.get_renderer()
        self.title_w = []
        for txt, _col, size, weight in TITLE_PARTS:
            t = self.fig.text(0, 0, txt, fontsize=size, fontweight=weight)
            self.title_w.append(t.get_window_extent(rend).width)
            t.remove()
        total = sum(self.title_w) + TITLE_GAP * (len(TITLE_PARTS) - 1)
        self.title_x0 = (W - total) / 2

    # value at fractional index
    def at(self, arr, f):
        i = int(math.floor(f))
        if i >= self.n - 1:
            return arr[-1]
        return arr[i] + (arr[i + 1] - arr[i]) * (f - i)

    def frame(self, k):
        t = k / FPS
        fig = self.fig
        fig.clf()
        fig.patch.set_facecolor(BG)

        p = race_progress(t)
        f = p * (self.n - 1)
        i = int(math.floor(f))
        cur_d = self.at(self.d, f)
        xs = np.append(self.d[: i + 1], cur_d)
        ya = np.append(self.a[: i + 1], self.at(self.a, f))
        yg = np.append(self.g[: i + 1], self.at(self.g, f))

        finale = clamp((t - INTRO - RACE) / 0.8)  # 0..1 over first 0.8 s of finale

        # ---- axes & limits
        ax = fig.add_axes([AX_PX[0] / W, AX_PX[1] / H, AX_PX[2] / W, AX_PX[3] / H])
        ax.set_facecolor(BG)
        for s in ax.spines.values():
            s.set_visible(False)
        # keep the arrow tips at TIP_FRAC of the width from the very first frame
        width = max(cur_d - self.d[0], 75.0) / TIP_FRAC
        xmin = min(self.d[0], cur_d - TIP_FRAC * width)
        ax.set_xlim(xmin, xmin + width)

        hi_target = max(ya.max(), yg.max()) * 1.10
        lo_target = min(ya.min(), yg.min()) * 0.90
        k_s = 0.18 if k else 1.0
        self.y_hi += (hi_target - self.y_hi) * k_s
        self.y_lo += (lo_target - self.y_lo) * k_s
        cur_max = max(ya[-1], yg[-1])
        self.y_hi = max(self.y_hi, cur_max * 1.06)
        self.y_lo = min(self.y_lo, min(ya[-1], yg[-1]) * 0.94)
        ax.set_ylim(self.y_lo, self.y_hi)

        # grid + y labels
        ax.tick_params(length=0, colors=MUTED, labelsize=24)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(money_short))
        ax.yaxis.tick_left()
        ax.grid(axis="y", color=GRID, lw=1.5)
        ax.set_xticks([])
        for lab in ax.get_yticklabels():
            lab.set_horizontalalignment("left")
            lab.set_x(0.005)
            lab.set_verticalalignment("bottom")
            lab.set_color("#5b6070")
        ax.tick_params(axis="y", pad=-6)

        # big faded year watermark
        year = str(int(np.datetime64(int(cur_d), "D").astype("datetime64[Y]").astype(int) + 1970))
        if t >= INTRO:
            ax.text(0.5, 0.45, year, transform=ax.transAxes, ha="center", va="center",
                    fontsize=250, fontweight="bold", color=TEXT, alpha=0.06, zorder=0)

        # $1,000 baseline
        ax.axhline(1000, color=MUTED, lw=2, ls=(0, (6, 6)), alpha=0.5, zorder=1)
        ax.text(0.01, 1000, "  $1,000 start", transform=ax.get_yaxis_transform(),
                va="top", ha="left", fontsize=22, color=MUTED, alpha=0.8)

        # ---- lines with glow
        dim = 1 - 0.35 * finale
        for y, col, z in ((yg, GOLD, 3), (ya, STOCK, 4)):
            for lw, al in ((16, 0.05), (9, 0.10), (5, 0.25)):
                ax.plot(xs, y, color=col, lw=lw, alpha=al * dim, solid_capstyle="round", zorder=z)
            ax.plot(xs, y, color=col, lw=3.6, alpha=dim, solid_capstyle="round", zorder=z + 0.5)

        # ---- arrow heads + value tags (pixel space)
        tips = {}
        show = clamp((t - INTRO + 0.15) / 0.3)   # arrows/tags appear as the countdown ends
        for key, y, col in (("stock", ya, STOCK), ("gold", yg, GOLD)):
            pts = ax.transData.transform(np.column_stack([xs[-120:], y[-120:]]))
            tip = pts[-1]
            sm = pts.copy()
            if len(pts) > 12:  # direction from a smoothed path so the arrow doesn't jitter
                kern = np.ones(9) / 9
                sm[:, 1] = np.convolve(np.pad(pts[:, 1], 4, mode="edge"), kern, mode="valid")
            back = sm[0]
            for q in sm[::-1]:
                if tip[0] - q[0] >= 60:
                    back = q
                    break
            v = np.array([tip[0], sm[-1][1]]) - back
            ang = math.atan2(v[1], v[0]) if np.hypot(*v) > 1e-6 else 0.0
            if k == 0 or t < INTRO:
                ang = 0.0
            self.angle[key] += (ang - self.angle[key]) * (0.3 if k else 1.0)
            draw_arrow(fig, tip, self.angle[key], col, alpha=show * (1 - finale))
            tips[key] = tip

        # tag positions, pushed apart if overlapping
        ya_px, yg_px = tips["stock"][1], tips["gold"][1]
        min_gap = 112
        if abs(ya_px - yg_px) < min_gap:
            mid = (ya_px + yg_px) / 2
            hi_first = ya_px >= yg_px
            ya_px = mid + (min_gap / 2 if hi_first else -min_gap / 2)
            yg_px = mid - (min_gap / 2 if hi_first else -min_gap / 2)
        for key, ypx, col, name, val in (("stock", ya_px, STOCK, NAME, ya[-1]),
                                         ("gold", yg_px, GOLD, "GOLD", yg[-1])):
            x0 = tips[key][0] + 40
            if finale < 1 and show > 0:
                fig.text(x0 / W, (ypx + 22) / H, name, color=col, fontsize=24, fontweight="bold",
                         va="center", alpha=show * (1 - finale))
                fig.text(x0 / W, (ypx - 16) / H, f"${val:,.0f}", color=TEXT, fontsize=40,
                         fontweight="heavy", va="center", alpha=show * (1 - finale))

        # ---- header
        x = self.title_x0
        for (txt, col, size, weight), w in zip(TITLE_PARTS, self.title_w):
            fig.text(x / W, 1 - TITLE_Y / H, txt, color=col, fontsize=size, fontweight=weight,
                     ha="left", va="center")
            x += w + TITLE_GAP
        fig.text(0.5, 1 - SUB_Y / H, self.subtitle, color=TEXT, fontsize=40,
                 fontweight="semibold", ha="center", va="center")
        date_str = pd.Timestamp(np.datetime64(int(cur_d), "D")).strftime("%b %Y")
        fig.text(0.5, 1 - DATE_Y / H, date_str.upper(), color=MUTED, fontsize=32,
                 fontweight="bold", ha="center", va="center")

        # ---- event caption
        for s, e, cap in self.events:
            if s <= cur_d <= e and finale == 0:
                fade = clamp(min(cur_d - s, e - cur_d) / 18)
                pill(fig, 0.5, 1 - PILL_Y / H, cap, fade)

        # ---- footer
        for y, line in zip(FOOTER_Y, self.footer):
            fig.text(0.5, 1 - y / H, line, color="#5b6070", fontsize=16, ha="center", va="center")

        # ---- 3-2-1 countdown before the race starts
        if t < INTRO:
            draw_countdown(fig, t)

        # ---- finale overlay
        if t >= INTRO + RACE:
            self.draw_finale(fig, t - INTRO - RACE, ya[-1], yg[-1])

        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
        return img

    def draw_finale(self, fig, ft, va, vg):
        ov = clamp(ft / 0.6)
        fig.patches.append(FancyBboxPatch((0, 1 - 1515 / H), 1, (1515 - 600) / H, boxstyle="square,pad=0",
                                          transform=fig.transFigure, fc=BG, ec="none",
                                          alpha=0.9 * ov, zorder=5))

        def card(appear, y, name, col, val, winner):
            a = ease_out((ft - appear) / 0.45)
            if a <= 0:
                return
            dy = (1 - a) * 40 / H
            # cards are centred and end at BTN_X so TikTok's buttons never cover them
            x1 = (BTN_X - 14) / W            # 14 px margin for the border stroke
            x0 = 1 - x1                      # symmetric around the centre
            box = FancyBboxPatch((x0, y - 0.058 - dy), x1 - x0, 0.116,
                                 boxstyle="round,pad=0,rounding_size=0.02",
                                 transform=fig.transFigure, fc="#11131b",
                                 ec=col, lw=4 if winner else 2, alpha=a, zorder=6,
                                 mutation_aspect=W / H)
            fig.patches.append(box)
            pct = (val / 1000 - 1) * 100
            fig.text(x0 + 0.035, y + 0.022 - dy, name, color=col, fontsize=40, fontweight="heavy",
                     va="center", alpha=a, zorder=7)
            fig.text(x0 + 0.035, y - 0.022 - dy, f"{pct:+,.0f}%",
                     color=ACCENT_UP if pct >= 0 else ACCENT_DOWN, fontsize=34,
                     fontweight="bold", va="center", alpha=a, zorder=7)
            fig.text(x1 - 0.035, y - dy, f"${val:,.0f}", color=TEXT, fontsize=64, fontweight="heavy",
                     ha="right", va="center", alpha=a, zorder=7)
            if winner:
                wa = ease_out((ft - appear - 0.6) / 0.35)
                if wa > 0:
                    s = 1 + 0.25 * (1 - wa)
                    fig.text(0.5, y + 0.072 - dy, "WINNER", color=BG, fontsize=30 * s,
                             fontweight="heavy", ha="center", va="center", alpha=wa, zorder=8,
                             bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.8", fc=col,
                                       ec="none", alpha=wa))

        # loser appears first at the bottom, winner second on top
        top, bottom = 1 - 790 / H, 1 - 1075 / H
        if va >= vg:
            card(0.9, bottom, "GOLD", GOLD, vg, False)
            card(1.5, top, NAME, STOCK, va, True)
        else:
            card(0.9, bottom, NAME, STOCK, va, False)
            card(1.5, top, "GOLD", GOLD, vg, True)

        qa = ease_out((ft - 2.3) / 0.5)
        if qa > 0:
            fig.text(0.5, 1 - 1330 / H, "Which one would you pick?", color=TEXT, fontsize=34,
                     fontweight="heavy", ha="center", va="center", alpha=qa, zorder=7)
            fig.text(0.5, 1 - 1395 / H, f"Comment GOLD or {NAME}", color=MUTED, fontsize=28,
                     fontweight="semibold", ha="center", va="center", alpha=qa, zorder=7)


COUNT_R, COUNT_SIZE = 150, 170   # ring radius (px) and digit font size
COUNT_INK = {}                    # digit -> (dx, dy) ink-centre offset at COUNT_SIZE, px


def measure_countdown_digits():
    """Measure where each digit's ink really sits relative to its text anchor.

    Text centring uses the font's line box, not the visible glyph, so digits look
    off-centre in the ring. We render each digit once and store the correction.
    """
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="black")
    for n in "123":
        fig.clf()
        fig.text(0.5, 0.5, n, color="white", fontsize=COUNT_SIZE, fontweight="heavy",
                 ha="center", va="center")
        fig.canvas.draw()
        ink = np.asarray(fig.canvas.buffer_rgba())[:, :, 0] > 128
        ys, xs = np.where(ink)
        # dx: ink right of anchor (+); dy: ink below anchor in image rows (+)
        COUNT_INK[n] = ((xs.min() + xs.max()) / 2 - W / 2, (ys.min() + ys.max()) / 2 - H / 2)
    plt.close(fig)


def draw_countdown(fig, t):
    """Big 3 / 2 / 1 with a draining ring, exactly in the centre of the frame."""
    n = int(INTRO - math.floor(t))          # 3, 2, 1
    u = t - math.floor(t)                   # 0..1 within this number
    cx, cy = W / 2, H / 2
    pop = ease_out(u / 0.25)
    scale = 1.35 - 0.35 * pop
    alpha = pop * (1 - clamp((u - 0.82) / 0.18))
    r = COUNT_R
    # backdrop hides the chart behind the ring; fades out as the race starts
    bg_a = 1 - clamp((t - (INTRO - 0.2)) / 0.2)
    fig.patches.append(Circle((cx, cy), r + 30, transform=IdentityTransform(), fc=BG,
                              ec="none", alpha=bg_a, zorder=11))
    fig.patches.append(Circle((cx, cy), r, transform=IdentityTransform(), fill=False,
                              ec=GRID, lw=10, alpha=alpha, zorder=12))
    col = (GOLD, STOCK, ACCENT_UP)[3 - n]
    fig.patches.append(Arc((cx, cy), 2 * r, 2 * r, theta1=90, theta2=90 + 360 * (1 - u) + 1e-3,
                           transform=IdentityTransform(), ec=col, lw=10, alpha=alpha, zorder=13))
    dx, dy = COUNT_INK[str(n)]
    fig.text((cx - dx * scale) / W, (cy + dy * scale) / H, str(n), color=TEXT,
             fontsize=COUNT_SIZE * scale, fontweight="heavy", ha="center", va="center",
             alpha=alpha, zorder=14)


def money_short(v, _pos=None):
    if v >= 1000:
        s = f"{v / 1000:.2f}".rstrip("0").rstrip(".")
        return f"${s}k"
    return f"${v:,.0f}"


def draw_arrow(fig, tip, ang, col, alpha=1.0, length=46, width=40):
    c, s = math.cos(ang), math.sin(ang)
    fwd, nrm = np.array([c, s]), np.array([-s, c])
    apex = tip + fwd * (length * 0.55)
    base = tip - fwd * (length * 0.45)
    pts = np.array([apex, base + nrm * width / 2, base - nrm * width / 2])
    for grow, al in ((1.6, 0.12), (1.25, 0.25)):
        ctr = pts.mean(axis=0)
        fig.patches.append(Polygon(ctr + (pts - ctr) * grow, closed=True, transform=IdentityTransform(),
                                   fc=col, ec="none", alpha=al * alpha, zorder=9))
    fig.patches.append(Polygon(pts, closed=True, transform=IdentityTransform(),
                               fc=col, ec="none", alpha=alpha, zorder=10))


def pill(fig, x, y, text, alpha, max_w=SAFE_RIGHT - SAFE_LEFT - 20):
    """Caption bubble; the font shrinks if the box would leave the safe zone."""
    size = 34
    t = fig.text(x, y, text, color=TEXT, fontsize=size, fontweight="bold", ha="center",
                 va="center", alpha=alpha, zorder=6,
                 bbox=dict(boxstyle="round,pad=0.55,rounding_size=0.9", fc="#1a1d28",
                           ec="#2c3142", lw=2, alpha=alpha))
    w = t.get_window_extent(fig.canvas.get_renderer()).width
    if w > max_w:
        t.set_fontsize(size * max_w / w)


# ---------------------------------------------------------------- audio
def make_audio(path, renderer):
    sr = 44100
    n = int(TOTAL * sr)
    out = np.zeros(n)
    tt = np.arange(n) / sr

    def add(sig, at):
        i = int(at * sr)
        j = min(n, i + len(sig))
        if i < n:
            out[i:j] += sig[: j - i]

    def env(dur, attack=0.005, decay=None):
        m = int(dur * sr)
        e = np.ones(m)
        a = max(1, int(attack * sr))
        e[:a] = np.linspace(0, 1, a)
        if decay:
            e *= np.exp(-np.arange(m) / (decay * sr))
        return e

    rng = np.random.default_rng(7)
    race_end = INTRO + RACE

    # pulse: kick on beats, hat on off-beats, tempo 112 -> 132 bpm over race
    beat_t, bpm = INTRO, 112.0
    while beat_t < race_end:
        m = int(0.35 * sr)
        x = np.arange(m) / sr
        freq = 45 + 75 * np.exp(-x * 30)
        kick = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-x * 9)
        add(0.55 * kick, beat_t)
        step = 60 / bpm
        hat = rng.standard_normal(int(0.05 * sr)) * env(0.05, 0.001, 0.012)
        hat = np.diff(hat, prepend=0)  # crude high-pass
        add(0.12 * hat, beat_t + step / 2)
        beat_t += step
        bpm = 112 + 20 * clamp((beat_t - INTRO) / RACE)

    # pad drone (A minor-ish) under the race
    pad = np.zeros(n)
    for fq, amp in ((110, 0.05), (164.8, 0.035), (220, 0.03), (261.6, 0.02)):
        pad += amp * np.sin(2 * np.pi * fq * tt + 0.3 * np.sin(2 * np.pi * 0.2 * tt))
    pad_env = np.clip((tt - 0.2) / 1.0, 0, 1) * np.clip((race_end + 0.2 - tt) / 0.4, 0, 1)
    out += pad * pad_env

    # tick on each new year
    years = pd.DatetimeIndex(renderer.idx).year
    first_idx = [np.argmax(years == y) for y in sorted(set(years))[1:]]
    for fi in first_idx:
        p = fi / (renderer.n - 1)
        # invert race_progress numerically
        ts = np.linspace(INTRO, race_end, 4000)
        pr = np.array([race_progress(x) for x in ts])
        at = ts[np.searchsorted(pr, p)]
        m = int(0.12 * sr)
        x = np.arange(m) / sr
        add(0.22 * np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 40), at)

    # countdown beeps (3, 2, 1) and a higher "go" beep when the race starts
    for i in range(int(INTRO)):
        m = int(0.18 * sr)
        x = np.arange(m) / sr
        add(0.35 * np.sin(2 * np.pi * 880 * x) * np.exp(-x * 14), float(i))
    m = int(0.45 * sr)
    x = np.arange(m) / sr
    add(0.4 * np.sin(2 * np.pi * 1760 * x) * np.exp(-x * 7), INTRO)

    # riser into the finale
    rs, rd = race_end - 2.0, 2.0
    m = int(rd * sr)
    x = np.arange(m) / sr
    noise = rng.standard_normal(m)
    riser = (noise * 0.5 + np.sin(2 * np.pi * (200 + 600 * (x / rd) ** 2) * x)) * (x / rd) ** 2
    add(0.12 * riser, rs)

    # impact at finale + reveal chimes
    m = int(1.6 * sr)
    x = np.arange(m) / sr
    boom = np.sin(2 * np.pi * (38 + 50 * np.exp(-x * 6)) * x) * np.exp(-x * 2.5)
    add(0.8 * boom + 0.15 * rng.standard_normal(m) * np.exp(-x * 14), race_end)
    for at, base in ((race_end + 0.9, 523.3), (race_end + 1.5, 659.3), (race_end + 2.1, 784.0)):
        m = int(1.2 * sr)
        x = np.arange(m) / sr
        tone = sum(np.sin(2 * np.pi * base * h * x) / h for h in (1, 2, 3)) * np.exp(-x * 3.5)
        add(0.16 * tone, at)

    # outro pad + master fade
    tail = np.clip((tt - race_end - 0.5) / 1.0, 0, 1)
    out += tail * 0.04 * (np.sin(2 * np.pi * 220 * tt) + np.sin(2 * np.pi * 329.6 * tt))
    out *= np.clip((TOTAL - tt) / 0.8, 0, 1)
    out = np.tanh(out * 1.2) * 0.9
    pcm = (out * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", nargs="?", default="AAPL", help=f"one of {', '.join(STOCKS)}")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    configure(args.ticker.upper())
    OUT_DIR.mkdir(exist_ok=True)
    r = Renderer()

    if args.preview:
        wanted = {0: "intro", int(1.1 * FPS): "count2", int(2.5 * FPS): "count1", int(9 * FPS): "mid", int(22 * FPS): "late",
                  int((INTRO + RACE + 2.8) * FPS): "finale"}
        for k in range(max(wanted) + 1):
            img = r.frame(k)
            if k in wanted:
                plt.imsave(OUT_DIR / f"preview_{wanted[k]}.png", img)
        print("previews written")
        return

    first = r.frame(0)
    r = Renderer()  # reset smoothing state
    wav = OUT_DIR / "audio.wav"
    make_audio(wav, r)
    mp4 = OUT_DIR / f"gold_vs_{TICKER.lower()}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fade_start = N_FRAMES - int(LOOP_FADE * FPS)
    for k in range(N_FRAMES):
        img = r.frame(k)
        if k >= fade_start:  # cross-fade back to frame 0 so the short loops cleanly
            # never reaches 1: frame 0 of the next play is the last step (no duplicate frame)
            a = (k - fade_start + 1) / (N_FRAMES - fade_start + 1)
            img = (img * (1 - a) + first * a).astype(np.uint8)
        proc.stdin.write(img.tobytes())
        if k % 90 == 0:
            print(f"frame {k}/{N_FRAMES}", flush=True)
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    print("wrote", mp4)


if __name__ == "__main__":
    main()

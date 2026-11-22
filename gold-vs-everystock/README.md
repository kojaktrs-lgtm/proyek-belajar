# Gold vs Everystock — vertical line-race shorts

Each video races $1,000 in gold (GLD ETF) against $1,000 in one stock over
10 years: 3-2-1 countdown, line race with arrow tips and event captions,
results cards, and a seamless loop. 1080×1920, 30 fps, ~29 s, generated
music/SFX. The layout stays inside the TikTok/Shorts safe zone.

| Video | Result (Nov 21, 2016 – Nov 19, 2026) |
|---|---|
| `output/gold_vs_aapl.mp4` | Apple $13,608 vs Gold $2,900 |
| `output/gold_vs_nke.mp4`  | Nike $774 vs Gold $2,900 |

```bash
pip install matplotlib pandas numpy
python fetch_data.py NKE            # -> data/prices_NKE.csv (+ key stats)
python make_video.py NKE --preview  # still frames for checking the layout
python make_video.py NKE            # -> output/gold_vs_nke.mp4
python check_safe_zone.py NKE       # verify nothing sits under TikTok/Shorts UI
```

## Adding a new stock
1. `python fetch_data.py TICKER` and read the printed stats.
2. Add an entry to `stocks.py` (display name, colour, event captions).
   Every caption must be true on every day it is shown — check it in the data.
3. Preview, render, then run `check_safe_zone.py`.

Data: daily closes from the public `alm0421/alm0421` GitHub dataset.
Stocks use adjusted close (dividends reinvested); GLD pays no dividends.

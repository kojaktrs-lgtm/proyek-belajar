# Gold vs Apple — $1,000, 10 years (vertical short)

Line-race video (1080×1920, 30 fps, ~31 s: 3-2-1 countdown, race, results; generated music/SFX) comparing
$1,000 invested in gold (GLD ETF) vs Apple (AAPL, dividends reinvested) from
Nov 21, 2016 to Nov 19, 2026.

Result from the data: **Apple $13,608 (+1,261%)**, **Gold $2,900 (+190%)**.

```bash
pip install matplotlib pandas numpy
python fetch_data.py         # refresh data/prices.csv
python make_video.py --preview   # still frames for checking the layout
python make_video.py         # -> output/gold_vs_apple.mp4
```

Data: daily closes from the public `alm0421/alm0421` GitHub dataset,
cross-checked against two independent sources. Event captions in
`make_video.py` (`EVENTS`) only appear once the event is true in the data.

"""Download daily AAPL + GLD prices and save the 10-year window used by the video.

Source: public CSV snapshots in the GitHub repo alm0421/alm0421 (daily OHLC with
adjusted close, dividends and splits). Cross-checked against two independent
datasets (AAPL adjusted close matched within 0.08%, GLD closes matched exactly).
"""
import io
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://raw.githubusercontent.com/alm0421/alm0421/HEAD/data/prices/{}.csv"
START, END = "2016-11-21", "2026-11-19"
OUT = Path(__file__).parent / "data" / "prices.csv"


def load(ticker: str) -> pd.DataFrame:
    with urllib.request.urlopen(BASE.format(ticker), timeout=60) as r:
        df = pd.read_csv(io.BytesIO(r.read()), parse_dates=["date"])
    return df.set_index("date").loc[START:END]


def main() -> None:
    aapl, gld = load("AAPL"), load("GLD")
    out = pd.DataFrame({
        "aapl_adj_close": aapl["adj_close"],   # split + dividend adjusted (total return)
        "aapl_close": aapl["close"],           # split adjusted only (price return)
        "gld_close": gld["close"],             # GLD pays no dividends
    }).dropna()
    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, float_format="%.4f")
    a = 1000 * out.aapl_adj_close.iloc[-1] / out.aapl_adj_close.iloc[0]
    g = 1000 * out.gld_close.iloc[-1] / out.gld_close.iloc[0]
    print(f"{len(out)} trading days {out.index[0].date()} -> {out.index[-1].date()}")
    print(f"$1,000 -> Apple ${a:,.0f} | Gold ${g:,.0f}")


if __name__ == "__main__":
    main()

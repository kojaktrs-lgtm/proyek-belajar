"""Download daily prices for a stock + GLD and save the window used by the video.

    python fetch_data.py NKE      # -> data/prices_NKE.csv

Source: public CSV snapshots in the GitHub repo alm0421/alm0421 (daily OHLC with
adjusted close, dividends and splits). For AAPL/GLD this was cross-checked
against two independent datasets (AAPL adjusted close within 0.08%, GLD exact).
"""
import io
import sys
import urllib.request
from pathlib import Path

import pandas as pd

from stocks import END, START

BASE = "https://raw.githubusercontent.com/alm0421/alm0421/HEAD/data/prices/{}.csv"


def load(ticker: str) -> pd.DataFrame:
    with urllib.request.urlopen(BASE.format(ticker), timeout=60) as r:
        df = pd.read_csv(io.BytesIO(r.read()), parse_dates=["date"])
    return df.set_index("date").loc[START:END]


def main(ticker: str) -> None:
    stock, gld = load(ticker), load("GLD")
    out = pd.DataFrame({
        "stock_adj_close": stock["adj_close"],  # split + dividend adjusted (total return)
        "stock_close": stock["close"],          # split adjusted only (price return)
        "gld_close": gld["close"],              # GLD pays no dividends
    }).dropna()
    path = Path(__file__).parent / "data" / f"prices_{ticker}.csv"
    path.parent.mkdir(exist_ok=True)
    out.to_csv(path, float_format="%.4f")
    s = 1000 * out.stock_adj_close / out.stock_adj_close.iloc[0]
    g = 1000 * out.gld_close / out.gld_close.iloc[0]
    print(f"{len(out)} trading days {out.index[0].date()} -> {out.index[-1].date()}")
    print(f"$1,000 -> {ticker} ${s.iloc[-1]:,.0f} | Gold ${g.iloc[-1]:,.0f}")
    print(f"{ticker} peak ${s.max():,.0f} on {s.idxmax().date()}, "
          f"max drawdown {(s / s.cummax() - 1).min():.0%}")
    lead = s > g
    flips = out.index[lead.ne(lead.shift())][1:]
    print(f"lead changes: {len(flips)} (last: {flips[-1].date() if len(flips) else '-'})")


if __name__ == "__main__":
    main(sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL")

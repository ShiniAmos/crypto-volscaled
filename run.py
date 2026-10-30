"""Backtest the strategy and print the result.

    python run.py                 # BTC + ETH, 2020 to now
    python run.py --since 2022-01-01
    python run.py --coins BTCUSDT,ETHUSDT,SOLUSDT --target-vol 0.5
"""

import argparse

import pandas as pd

import data
from strategy import Params, backtest, metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", default="BTCUSDT,ETHUSDT")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD")
    ap.add_argument("--target-vol", type=float, default=0.40)
    ap.add_argument("--refresh", action="store_true", help="re-download the candles")
    a = ap.parse_args()

    coins = tuple(c.strip().upper() for c in a.coins.split(","))
    p = Params(coins=coins, target_vol=a.target_vol)
    px = data.closes(coins, refresh=a.refresh)
    if a.since:
        px = px[a.since:]

    eq, expo, turn = backtest(px, p)
    m = metrics(eq, expo)

    print(f"{', '.join(coins)}   {px.index[0].date()} -> {px.index[-1].date()}   "
          f"target vol {p.target_vol:.0%}   costs {p.cost:.2%}/side\n")
    print(f"  CAGR              {m['cagr']:+8.2%}")
    print(f"  Sharpe            {m['sharpe']:8.3f}")
    print(f"  max drawdown      {m['max_drawdown']:+8.2%}")
    print(f"  average exposure  {m['avg_exposure']:8.1%}")
    print(f"  months in profit  {m['pct_months_green']:8.1%}")
    print(f"  total return      {m['total_return']:+8.2%}")

    # buy and hold, equally weighted, for comparison - the number that must be beaten
    bh = (px / px.iloc[0]).mean(axis=1)
    bh_dd = (bh / bh.cummax() - 1).min()
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    print(f"\n  for comparison, holding the same coins equally weighted:")
    print(f"    CAGR {bh.iloc[-1] ** (1 / yrs) - 1:+.2%}   max drawdown {bh_dd:+.2%}")


if __name__ == "__main__":
    main()

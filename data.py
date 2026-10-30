"""Binance 4-hour candles, cached to disk. No API key needed - these are public endpoints."""

import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.binance.com/api/v3/klines"
CACHE = Path(__file__).parent / "data"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_buy_volume", "taker_buy_quote", "ignore"]


def fetch(symbol: str, interval="4h", start_ms=None) -> pd.DataFrame:
    """Every candle from `start_ms` to now, paged 1000 at a time."""
    out, cur = [], start_ms or int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000)
    while True:
        r = requests.get(BASE, params={"symbol": symbol, "interval": interval,
                                       "startTime": cur, "limit": 1000}, timeout=30)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        out += rows
        cur = rows[-1][0] + 1
        if len(rows) < 1000:
            break
        time.sleep(0.25)          # stay well inside the public rate limit
    df = pd.DataFrame(out, columns=COLS)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    df["t"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df.set_index("t").sort_index()


def load(symbol: str, interval="4h", refresh=False) -> pd.DataFrame:
    """Cached candles. Delete the parquet, or pass refresh=True, to re-download."""
    CACHE.mkdir(exist_ok=True)
    path = CACHE / f"{symbol}_{interval}.parquet"
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    df = fetch(symbol, interval)
    df.to_parquet(path)
    return df


def closes(symbols, interval="4h", refresh=False) -> pd.DataFrame:
    """One column of closing prices per symbol, aligned on a shared index."""
    frames = {s: load(s, interval, refresh)["close"] for s in symbols}
    return pd.DataFrame(frames).dropna()

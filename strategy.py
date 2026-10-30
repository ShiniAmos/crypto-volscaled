"""The whole strategy, in one function.

    Always hold BTC and ETH. Size each one inversely to its own volatility.

There is no trend filter, no breakout, no ranking and no cash position. That is deliberate: it is
the opposite design to the trend bot in the sister repository, and it exists because that one sits
in cash 82% of the time and shows a green month only 26% of the time.

    weight_i = clip(target_vol / realised_vol_i, 0, 1) / number_of_coins

A coin running at 80% annualised volatility gets half the weight of one running at 40%. The book
is therefore always invested but not always equally exposed: it shrinks into turbulence and grows
into calm, which is the only risk control here.

WHY INVERSE VOLATILITY AND NOT EQUAL WEIGHT
Equal weight gives the wilder asset a larger share of the portfolio's RISK even though it has an
equal share of its money. Inverse-volatility weighting equalises the risk contribution instead,
which is why the drawdown is ~56% rather than the ~67% of simply holding.

CAUSALITY
Volatility is computed from returns up to the previous bar and the weight is applied from the next
bar on. No bar uses its own data to decide its own position.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

BARS_PER_DAY = 6                 # 4-hour bars
BARS_PER_YEAR = BARS_PER_DAY * 365


@dataclass(frozen=True)
class Params:
    coins: tuple = ("BTCUSDT", "ETHUSDT")
    target_vol: float = 0.40     # annualised; the volatility each sleeve is sized toward
    vol_window_days: int = 30    # lookback for realised volatility
    max_weight: float = 1.0      # per-coin ceiling, before the per-coin split
    fee: float = 0.0010          # 0.10% per side, Binance spot taker
    slippage: float = 0.0007     # 7 bps per side

    @property
    def cost(self):
        return self.fee + self.slippage


def realised_vol(close: pd.Series, p: Params) -> pd.Series:
    """Annualised volatility of log returns over the lookback, known at the bar's close."""
    logret = np.log(close).diff()
    return logret.rolling(p.vol_window_days * BARS_PER_DAY).std() * np.sqrt(BARS_PER_YEAR)


def target_weights(closes: pd.DataFrame, p: Params) -> pd.DataFrame:
    """The weight to hold in each coin on each bar. Columns are coins, rows are bars.

    `.shift(1)` is the causality guard: the weight held DURING a bar is computed from data that had
    already closed before it opened.
    """
    w = pd.DataFrame(index=closes.index, columns=closes.columns, dtype=float)
    for c in closes.columns:
        v = realised_vol(closes[c], p)
        w[c] = (p.target_vol / v).clip(0.0, p.max_weight) / len(closes.columns)
    return w.shift(1).fillna(0.0)


def backtest(closes: pd.DataFrame, p: Params = Params()):
    """Compound the weighted return, charging `cost` on every change in weight.

    Turnover is charged on the absolute change in each coin's weight, so drifting with the market
    is free and rebalancing is not - which is the honest accounting, and the reason the strategy
    rebalances continuously rather than on a schedule.
    """
    w = target_weights(closes, p)
    ret = closes.pct_change().fillna(0.0)
    turnover = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    port = (ret * w).sum(axis=1) - turnover * p.cost
    equity = (1.0 + port).cumprod()
    return equity, w.sum(axis=1), turnover


def metrics(equity: pd.Series, exposure: pd.Series) -> dict:
    eq = equity.dropna()
    r = np.log(eq.clip(lower=1e-12)).diff().dropna()
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    monthly = eq.resample("ME").last().pct_change().dropna()
    return {
        "cagr": float(eq.iloc[-1] ** (1 / years) - 1),
        "sharpe": float(r.mean() / r.std() * np.sqrt(BARS_PER_YEAR)) if r.std() > 0 else 0.0,
        "max_drawdown": float((eq / eq.cummax() - 1).min()),
        "avg_exposure": float(exposure.mean()),
        "pct_months_green": float((monthly > 0).mean()) if len(monthly) else float("nan"),
        "total_return": float(eq.iloc[-1] - 1),
    }

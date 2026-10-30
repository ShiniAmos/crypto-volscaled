"""The three things that would silently invalidate every number this repo prints."""

import numpy as np
import pandas as pd
import pytest

from strategy import Params, backtest, realised_vol, target_weights


def _closes(n=2000, vol_a=0.01, vol_b=0.03, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="4h", tz="UTC")
    a = 100 * np.exp(np.cumsum(rng.normal(0, vol_a, n)))
    b = 100 * np.exp(np.cumsum(rng.normal(0, vol_b, n)))
    return pd.DataFrame({"AAAUSDT": a, "BBBUSDT": b}, index=idx)


def test_the_wilder_coin_gets_the_smaller_weight():
    """The entire premise. BBB is three times as volatile as AAA."""
    px = _closes()
    w = target_weights(px, Params(coins=("AAAUSDT", "BBBUSDT")))
    tail = w.iloc[-500:]
    assert tail["BBBUSDT"].mean() < tail["AAAUSDT"].mean(), \
        "the more volatile coin was not sized down"


def test_no_bar_uses_its_own_data():
    """Causality. The weight held during a bar must be knowable before that bar opens."""
    px = _closes()
    p = Params(coins=("AAAUSDT", "BBBUSDT"))
    w = target_weights(px, p)
    manual = pd.DataFrame({c: (p.target_vol / realised_vol(px[c], p)).clip(0, 1) / 2
                           for c in px.columns}).shift(1).fillna(0.0)
    pd.testing.assert_frame_equal(w, manual)


def test_costs_are_actually_charged():
    """A backtest that forgets its fees is a brochure."""
    px = _closes()
    free = Params(coins=("AAAUSDT", "BBBUSDT"), fee=0.0, slippage=0.0)
    real = Params(coins=("AAAUSDT", "BBBUSDT"))
    eq_free, _, _ = backtest(px, free)
    eq_real, _, _ = backtest(px, real)
    assert eq_real.iloc[-1] < eq_free.iloc[-1], "costs made no difference"


def test_weights_never_exceed_one():
    """Spot only: the book can never be more than fully invested."""
    px = _closes(vol_a=0.001, vol_b=0.001)      # very calm: the cap must bind
    w = target_weights(px, Params(coins=("AAAUSDT", "BBBUSDT")))
    assert w.sum(axis=1).max() <= 1.0 + 1e-9, "the strategy levered up"


def test_a_flat_market_earns_nothing_and_loses_the_costs():
    idx = pd.date_range("2022-01-01", periods=1500, freq="4h", tz="UTC")
    px = pd.DataFrame({"AAAUSDT": 100.0, "BBBUSDT": 100.0}, index=idx)
    eq, _, _ = backtest(px, Params(coins=("AAAUSDT", "BBBUSDT")))
    assert eq.iloc[-1] <= 1.0 + 1e-9

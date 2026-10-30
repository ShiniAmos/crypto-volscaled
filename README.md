# crypto-volscaled

Always hold BTC and ETH. Size each one inversely to its own volatility. That is the entire
strategy — there is no trend filter, no breakout, no ranking, and the book is never in cash.

```
weight_i = clip(target_vol / realised_vol_i, 0, 1) / number_of_coins
```

A coin running at 80% annualised volatility gets half the weight of one at 40%. The portfolio
shrinks into turbulence and grows into calm, and that is the only risk control.

## Why this exists

It is the deliberate opposite of its sister repository
([crypto-trend-bot](../crypto-trend-bot)), which sits in cash 82% of the time and shows a green
month only 26% of the time. This one is invested ~75% of the time and is green in **56%** of
months. It is here to make that trade-off concrete rather than arguable.

## Results

BTC + ETH, 4-hour bars, 2022-01-01 to 2026-10-04, with 0.10% fees and 7 bps slippage charged on
every change in weight:

| | this strategy | holding the same coins equally |
|---|---|---|
| CAGR | **+14.12%** | +5.19% |
| max drawdown | **−55.59%** | −69.25% |
| Sharpe | 0.347 | — |
| average exposure | 74.9% | 100% |
| months in profit | **56.1%** | — |
| total return | +87.44% | — |

Reproduce it:

```bash
pip install -r requirements.txt
python run.py --since 2022-01-01
```

The candles download from Binance's public API on first run and cache to `data/`. No API key is
needed and nothing here places an order.

## Read this before you take the numbers seriously

**A −55% drawdown is the headline, not the CAGR.** On $1,000 that is watching it fall to $445 and
sitting through it. Most people do not, which is why the drawdown matters more than the return.

**Two coins is not diversification.** BTC and ETH fall together. Inverse-volatility weighting
equalises their *risk* contributions; it does nothing about their correlation.

**The sample is one bull market and one bear.** 2022–2026 contains a single full cycle. Four and a
half years of crypto is not a large sample, and the strategy has never been run forward on money.

**A known discrepancy, stated rather than buried.** The research harness in the sister repository
reports +9.72% CAGR for this same idea over the same window, against the +14.12% this code
produces. Drawdown, exposure and green-month share agree almost exactly (−55.59%, ~75%, 56.1%), so
the difference is in return accounting — most likely index alignment and NaN handling between a
383-coin panel and this two-column one. It is unresolved. Treat the lower figure as the
conservative one.

## Layout

```
strategy.py   the strategy: ~40 lines of actual logic
data.py       Binance public candles, cached to parquet
run.py        backtest and print
tests/        5 tests covering the things that would silently invalidate the numbers
```

The tests are the part worth reading first. They check that the more volatile coin really does get
the smaller weight, that no bar uses its own data to decide its own position, that costs are
actually charged, and that the strategy can never lever above fully invested.

## What this is not

Not advice, not a product, and not running anyone's money. It is one half of a measured comparison
between two opposite designs, published so the comparison can be checked.

## Licence

MIT.

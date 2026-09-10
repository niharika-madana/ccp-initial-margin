# CCP Initial Margin & Default-Fund Stress Engine
Design v0.1 · Sep 2026

## 1. Scope

**Purpose:** Implement a filtered-historical-simulation initial margin model for the CME Treasury futures complex, structured after CME's SPAN 2 framework; validate it for coverage and procyclicality; and extend the validated model to clearing-house-level default-fund adequacy under a Cover-2 standard.

**Research question:** Anti-procyclicality tools damp the responsiveness of initial margin to realised volatility. That damping is not free: it raises average margin in calm regimes, and members fund the difference continuously. Quantify the
trade-off(reduction in margin procyclicality against the increase in average margin) across the EMIR Article 28 tool set, holding 99% coverage as a binding constraint rather than an objective.

Products:  ZT, ZF, ZN, TN, ZB, UB(CME Treasury futures, 2y to ultra-long).
Window:    2010 → today. Covers Mar 2020, the 2022 rates selloff, Mar 2023.
Positions: synthetic. Three test portfolios early (long ZN, 2s30s steepener,
           5s10s30s butterfly), then 20–30 generated clearing members.

Not covered: options on futures; cross-margining vs cash Treasuries or repo; collateral haircuts and FX; liquidity stress (credit stress only); recovery tools past assessments; Cross Model Offset (legacy-SPAN books only).

## 2. Data

Source: Refinitiv Datastream Futures via WRDS, table `tr_ds_fut`.

Using `dsfutcontrval`,  one row per delivery contract per day.

| Product | contrcode | clscode | Coverage          | Contracts |
|---------|-----------|---------|-------------------|-----------|
| ZT      | 3377      | 2523    | 1990-06 → 2027-03 | 147 |
| ZF      | 2680      | 1997    | 1988-05 → 2027-03 | 156 |
| ZN      | 2682      | 3896    | 1982-05 → 2027-03 | 180 |
| TN      | 4361      | 4359    | 2016-01 → 2027-03 |  45 |
| ZB      | 3271      | 2441    | 1976-12 → 2027-03 | 202 |
| UB      | 2685      | 2001    | 2010-01 → 2027-03 |  69 |

These are the composite trading-class series. The electronic-only ones(CZN 458, CZT 463, CZF 452, CZB 448, CZU 2687) stop after Dec 2025, a daily pipeline built on them would have had no data from Jan 2026.

Sanity check that passed: contract counts match the Mar/Jun/Sep/Dec cycle exactly (ZF 39y x 4 = 156, observed 156). Launch dates in the data match the real CME launches of UB (2010) and TN (2016).

Fields: open, high, low, settlement, volume, open interest. No nulls.

Multipliers: from `dsfutcontrchg` (LotSize, TickValue, TickSize), read as-of-date. These change over time, so hardcoding today's values onto 2012 prices is wrong

Roll dates: `firstnoticedate` on `dsfutcontrinfo`. Present on ~100% of post-2009 contracts. For Treasury futures first notice comes BEFORE last trade, so rolling off last-trade is a different and wrong roll.

Curve data: FRED (DGS2, DGS5, DGS10, DGS30).

Not available:
- CRSP Treasuries: Not entitled, no CUSIP data, so no true cheapest-to-deliver. This forces price-space risk factors, which was the better choice anyway.
- Exchange margin history: Datastream margin fields are empty.

## 3. Model parameters

Risk factors: price-space, per contract per tenor rank (front, second).
Lookback:     2 years default. Grid {1y, 2y, 5y, 10y}(EMIR floor: 12 months).
Confidence:   99% default. Grid {99, 99.5}. EMIR floor: 99% listed, 99.5% OTC.
MPOR:         1 day default (CME listed). Grid {1, 2}. EMIR floor is 2.
EWMA lambda:  0.94 default (RiskMetrics). Grid {0.94, 0.97, 0.99}.
Blend x:      0.7 default. Grid {0.5, 0.7, 0.9}. No published consensus.
Stress agg:   max over the scenario set. Alternatives: mean, quantile.

Aggregation (CME published):
> margin = x*HVaR + (1-x)*SVaR + liquidity + concentration

## 4. Anti-procyclicality tools compared

From EMIR RTS 153/2013 Article 28. A CCP must adopt at least one of:
  1. 25% margin buffer, drawable when calculated margin rises sharply
  2. 25% weight on stressed observations in the lookback
  3. 10-year lookback volatility floor
  4. (control, non-EMIR) plain volatility floor

Cost measured:  average margin vs the unfloored FHS base
Metrics:        peak-to-trough ratio; worst 5-day and 30-day increase;
                frequency of daily increases >10%     [BoE FS Paper 29]
Constraint:     99% coverage holds (Kupiec + Christoffersen)

Jurisdiction note: these are European tools applied to US products. Deliberate —
the EMIR menu is the only concrete, testable APC specification published
anywhere. State it before an interviewer finds it.

## 5. Headline claim

"For a filtered-historical-simulation margin model on the CME Treasury complex
over 2010–2026, [TOOL] reduces [METRIC] from ___ to ___ at a cost of ___%
higher average margin, while maintaining 99% coverage."

## 6. Architecture

ingest/       WRDS contracts → Parquet (product/year) → DuckDB; FRED curve
riskfactor/   contract → (product, tenor rank), roll rule, MPOR returns,
              EWMA vol, stress-period tags
margin/       HVaR · SVaR · APC tools · liquidity · concentration · aggregation
members/      synthetic clearing members (exponential / uniform / whale),
              house and client books
stress/       scenario library (historical, antithetical, hypothetical, PCA)
              → per-member stressed loss over IM
fund/         Cover-2 / Cover-X sizing · waterfall · copula defaults ·
              reverse stress
validate/     Kupiec · Christoffersen · traffic light · sensitivity grid ·
              procyclicality metrics
orchestrate/  Dagster assets
dashboard/    Streamlit, read-only over DuckDB
configs/      model.yaml, validation.yaml, stress.yaml — parameters live here

Schedule:  daily   → ingest, risk factors, margin, exceptions, stress, Cover-2
           monthly → sensitivity grid (a partitioned asset)
           ad hoc  → validation report
Not arbitrary: PFMI Principles 4 and 6 require daily stress testing and daily
backtesting, with sensitivity analysis at least monthly.

Every asset keyed by a run id. Every output carries a manifest: config hash,
package versions, input partition versions.

Dagster over Airflow: assets are datasets, not tasks; partitioned assets give
the sensitivity grid and backfill for free; runs locally without a scheduler.

Python. A C++20 scenario-P&L kernel goes in at Week 11 only if profiling shows
Python is the bottleneck. A port with no speed number is signalling.

## 7. Licensing and reproducibility

WRDS data cannot be redistributed. So`data/raw/` is gitignored from commit one and results published as statistics and plots.
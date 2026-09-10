# CCP Initial Margin & Default-Fund Stress Engine

A filtered-historical-simulation initial margin model for the CME Treasury futures complex, structured after CME's SPAN 2 framework, validated for coverage and procyclicality, and extended to default-fund adequacy under Cover-2.

**Research question.** Anti-procyclicality tools damp initial margin's response to realised volatility. That damping is not free: it raises average margin in calm regimes, and members fund the difference continuously. How large is the
trade-off across the EMIR Article 28 tool set, holding 99% coverage as a binding constraint?

Design and parameter provenance: [`docs/design.md`](docs/design.md)

## Status: v0.0.1 (Week 1)

- Config schema with validation. EMIR RTS 153/2013 floors(confidence, lookback, and the Article 28 tool minima) are     enforced at load time, so the model cannot be run in a configuration that breaches them.
- `config_hash()` for run manifests: every result traces to the settings that produced it.
- Package layout, pytest + ruff in CI, Dagster code location initialised.

No data and no model yet.

## Data

Refinitiv Datastream Futures via WRDS (`tr_ds_fut`), individual delivery contracts. Not redistributable hence, `data/` is gitignored, and the repository is not runnable end to end without WRDS access.
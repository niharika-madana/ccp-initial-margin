"""Configuration schema and loader.

Regulatory floors from EMIR RTS (EU) 153/2013 are enforced here, at load time.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TRADING_DAYS_PER_YEAR = 252
EMIR_MIN_CONFIDENCE_LISTED = 0.99
EMIR_MIN_LOOKBACK_DAYS = 250          # "at least 12 months"
EMIR_MIN_BUFFER_PCT = 0.25            # Art. 28(a)
EMIR_MIN_STRESSED_WEIGHT = 0.25       # Art. 28(b)
EMIR_MIN_FLOOR_LOOKBACK_YEARS = 10    # Art. 28(c)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Product(Strict):
    symbol: str = Field(min_length=1)
    contrcode: int = Field(gt=0)
    clscode: int = Field(gt=0)


class Window(Strict):
    start: date
    end: date | None = None

    @model_validator(mode="after")
    def _ordered(self) -> Window:
        if self.end is not None and self.end <= self.start:
            raise ValueError("window.end must be after window.start")
        return self


class Roll(Strict):
    rule: Literal["first_notice", "last_trade"]
    offset_bd: int = Field(ge=0, le=30)


class RiskFactor(Strict):
    space: Literal["price", "yield"]
    tenor_ranks: list[int] = Field(min_length=1)
    roll: Roll

    @field_validator("tenor_ranks")
    @classmethod
    def _ranks(cls, v: list[int]) -> list[int]:
        if any(r < 1 for r in v):
            raise ValueError("tenor_ranks are 1-based; front month is 1")
        if len(set(v)) != len(v):
            raise ValueError("tenor_ranks must be unique")
        return sorted(v)


class Returns(Strict):
    mpor_days: int = Field(ge=1, le=10)


class Vol(Strict):
    method: Literal["ewma"]
    lambda_: float = Field(alias="lambda", gt=0.0, lt=1.0)

    @property
    def half_life_days(self) -> float:
        from math import log

        return log(0.5) / log(self.lambda_)


class HVaR(Strict):
    lookback_years: float = Field(gt=0)
    confidence: float = Field(lt=1.0)

    @field_validator("confidence")
    @classmethod
    def _emir_confidence(cls, v: float) -> float:
        if v < EMIR_MIN_CONFIDENCE_LISTED:
            raise ValueError(
                f"confidence {v} breaches the EMIR RTS 153/2013 floor of "
                f"{EMIR_MIN_CONFIDENCE_LISTED} for exchange-traded instruments"
            )
        return v

    @field_validator("lookback_years")
    @classmethod
    def _emir_lookback(cls, v: float) -> float:
        days = v * TRADING_DAYS_PER_YEAR
        if days < EMIR_MIN_LOOKBACK_DAYS:
            raise ValueError(
                f"lookback_years {v} is {days:.0f} trading days, below the EMIR "
                f"minimum of {EMIR_MIN_LOOKBACK_DAYS} (12 months)"
            )
        return v


class SVaR(Strict):
    aggregation: Literal["max", "mean", "quantile"]


class Blend(Strict):
    x: float | None = Field(default=None, ge=0.0, le=1.0)


class APC(Strict):
    tool: Literal["none", "buffer", "stressed_weight", "lookback_floor", "vol_floor"]
    buffer_pct: float = Field(ge=0.0, le=1.0)
    stressed_weight: float = Field(ge=0.0, le=1.0)
    floor_lookback_years: float = Field(gt=0)

    @model_validator(mode="after")
    def _article_28_minima(self) -> APC:
        """Art. 28 sets minima on whichever tool is selected, not on all of them."""
        if self.tool == "buffer" and self.buffer_pct < EMIR_MIN_BUFFER_PCT:
            raise ValueError(f"Art. 28(a) requires buffer_pct >= {EMIR_MIN_BUFFER_PCT}")
        if self.tool == "stressed_weight" and self.stressed_weight < EMIR_MIN_STRESSED_WEIGHT:
            raise ValueError(
                f"Art. 28(b) requires stressed_weight >= {EMIR_MIN_STRESSED_WEIGHT}"
            )
        if (
            self.tool == "lookback_floor"
            and self.floor_lookback_years < EMIR_MIN_FLOOR_LOOKBACK_YEARS
        ):
            raise ValueError(
                f"Art. 28(c) requires floor_lookback_years >= "
                f"{EMIR_MIN_FLOOR_LOOKBACK_YEARS}"
            )
        return self


class AddOn(Strict):
    enabled: bool


class AddOns(Strict):
    liquidity: AddOn
    concentration: AddOn


class ModelConfig(Strict):
    products: list[Product] = Field(min_length=1)
    window: Window
    risk_factor: RiskFactor
    returns: Returns
    vol: Vol
    hvar: HVaR
    svar: SVaR
    blend: Blend
    apc: APC
    addons: AddOns

    @field_validator("products")
    @classmethod
    def _unique_symbols(cls, v: list[Product]) -> list[Product]:
        symbols = [p.symbol for p in v]
        if len(set(symbols)) != len(symbols):
            raise ValueError("duplicate product symbols")
        return v

    def config_hash(self) -> str:
        """Stable 12-char digest of the resolved config.

        Goes into every run manifest, so any number in a report traces back to
        the exact settings that produced it.
        """
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def load_config(path: str | Path) -> ModelConfig:
    text = Path(path).read_text(encoding="utf-8")
    return ModelConfig(**yaml.safe_load(text))
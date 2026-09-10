from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from ccpmargin.config import ModelConfig, load_config

CONFIG_PATH = Path(__file__).parents[1] / "configs" / "model.yaml"


def _raw() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def test_shipped_config_loads():
    cfg = load_config(CONFIG_PATH)
    assert len(cfg.products) == 6
    assert cfg.blend.x is None, "blend.x must stay uncalibrated until Week 7"


def test_confidence_below_emir_floor_rejected():
    raw = _raw()
    raw["hvar"]["confidence"] = 0.95
    with pytest.raises(ValidationError, match="EMIR"):
        ModelConfig(**raw)


def test_lookback_below_twelve_months_rejected():
    raw = _raw()
    raw["hvar"]["lookback_years"] = 0.5
    with pytest.raises(ValidationError, match="EMIR"):
        ModelConfig(**raw)


def test_config_hash_is_stable_and_sensitive():
    a = load_config(CONFIG_PATH)
    b = load_config(CONFIG_PATH)
    assert a.config_hash() == b.config_hash()

    raw = _raw()
    raw["hvar"]["lookback_years"] = 5.0
    assert ModelConfig(**raw).config_hash() != a.config_hash()  
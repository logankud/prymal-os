"""
DSPy language model access.

Loads model class definitions from config/core.yaml and exposes get_lm()
for nodes and workers to bind specific LM instances to their predictors.

Usage:
    from kernel.model import get_lm
    self._predict = dspy.ChainOfThought(MySignature, lm=get_lm(ModelClass.CHEAP))

Model classes (fast, best, cheap) are defined in config/core.yaml.
Swap the underlying model string there without touching any node or worker code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import dspy
import yaml

from config.core import CoreConfig, ModelClass

_CONFIG_PATH = Path("config/core.yaml")


@lru_cache(maxsize=1)
def _load_config() -> CoreConfig:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            data = yaml.safe_load(f)
        return CoreConfig(**data)
    return CoreConfig()


@lru_cache(maxsize=None)
def get_lm(model_class: ModelClass) -> dspy.LM:
    """
    Return a cached dspy.LM instance for the given model class.

    Args:
        model_class: one of the keys defined under lm: in config/core.yaml
                     (e.g. "fast", "best", "cheap")

    Raises:
        ValueError: if model_class is not defined in config.
    """
    config = _load_config()
    model_string = config.lm.get(model_class)

    if model_string is None:
        available = sorted(config.lm.keys())
        raise ValueError(
            f"Unknown model class '{model_class}'. "
            f"Available classes: {available}. "
            f"Add it to config/core.yaml under lm:."
        )

    return dspy.LM(model_string)


def configure_lm() -> None:
    """
    Set the global DSPy default LM to the 'fast' model class.

    Called once at app startup as a fallback for any predictor
    that does not explicitly bind an LM via get_lm().
    """
    dspy.configure(lm=get_lm(ModelClass.FAST))

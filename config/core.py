"""
OpsIQ core configuration schema — mirrors config/core.yaml.

ModelClass defines the available LM tiers. Use these constants when
calling get_lm() in nodes and workers — never pass a raw string.

Swap the underlying model string in core.yaml to change which model
backs a class without touching any node or worker code.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ModelClass(StrEnum):
    """
    Semantic model tiers available across the system.

    CHEAP  — low-cost, high-throughput tasks (parsing, extraction, classification)
    FAST   — low-latency tasks where speed matters more than depth
    BEST   — highest capability for complex reasoning, planning, evaluation
    """
    CHEAP = "cheap"
    FAST  = "fast"
    BEST  = "best"


class CoreConfig(BaseModel):
    # Fallback defaults — source of truth is config/core.yaml.
    lm: dict[str, str] = {
        ModelClass.CHEAP: "openai/gpt-4o-mini",
        ModelClass.FAST:  "openai/gpt-4o-mini",
        ModelClass.BEST:  "openai/gpt-4o",
    }

"""
Pricing module for VLM providers.
Reads per-token pricing rates from providers.yaml registry.
"""

import logging
from pathlib import Path
import yaml
from typing import Dict

logger = logging.getLogger(__name__)

PRICING_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"

_cache: Dict[str, Dict[str, float]] | None = None


def _load_pricing() -> Dict[str, Dict[str, float]]:
    global _cache
    if _cache is not None:
        return _cache

    try:
        with open(PRICING_YAML) as f:
            config = yaml.safe_load(f)
    except Exception:
        _cache = {}
        return _cache

    result: Dict[str, Dict[str, float]] = {}
    for prov in config.get("providers", []):
        for model in prov.get("models", []):
            pricing = model.get("pricing")
            if pricing and isinstance(pricing, dict):
                result[model["id"]] = {
                    "input_per_1m": pricing.get("input_per_1m", 0.0),
                    "output_per_1m": pricing.get("output_per_1m", 0.0),
                }

    _cache = result
    return _cache


def clear_cache():
    global _cache
    _cache = None


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate estimated cost for a model call.

    Args:
        model: Model identifier (e.g. "qwen/qwen3.5-flash-02-23")
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    pricing = _load_pricing().get(model)
    if not pricing:
        logger.warning("No pricing data for model=%s, returning 0.0", model)
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
    return round(input_cost + output_cost, 6)

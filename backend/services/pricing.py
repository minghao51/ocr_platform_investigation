"""
Pricing module for VLM providers.
Contains per-token pricing rates for all supported models (2026 rates).
"""

from typing import Dict

# Pricing per 1M tokens (input, output) in USD
# Sources: provider pricing pages as of April 2026
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # OpenRouter models
    "qwen/qwen3.5-flash-02-23": {
        "input_per_1m": 0.065,
        "output_per_1m": 0.26,
    },
    "google/gemini-2.5-flash-lite": {
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
    },
    "google/gemini-3-flash-preview": {
        "input_per_1m": 0.50,
        "output_per_1m": 3.00,
    },
    "x-ai/grok-4.1-fast": {
        "input_per_1m": 0.20,
        "output_per_1m": 0.50,
    },
    "google/gemma-4-31b-it": {
        "input_per_1m": 0.13,
        "output_per_1m": 0.38,
    },
    # Gemini (direct API)
    "gemini-3.1-pro-preview": {
        "input_per_1m": 2.00,
        "output_per_1m": 12.00,
    },
    "gemini-3-flash-preview": {
        "input_per_1m": 0.15,
        "output_per_1m": 1.50,
    },
    "gemini-2.5-flash-lite": {
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
    },
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate estimated cost for a model call.

    Args:
        model: Model identifier (e.g. "Qwen/Qwen2.5-VL-72B-Instruct")
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output_per_1m"]
    return round(input_cost + output_cost, 6)


def get_model_pricing(model: str) -> Dict[str, float] | None:
    """Get pricing info for a model, or None if unknown."""
    return MODEL_PRICING.get(model)


def get_pricing_for_provider_models(provider: str) -> list[dict]:
    """
    Return pricing info for all known models of a provider.
    Each item: {id, input_per_1m, output_per_1m}
    """
    results = []
    for model_id, pricing in MODEL_PRICING.items():
        if provider == "openrouter" and "/" in model_id:
            results.append({"id": model_id, **pricing})
        elif provider == "gemini" and model_id.startswith("gemini-"):
            results.append({"id": model_id, **pricing})
        elif provider == "litellm":
            results.append({"id": model_id, **pricing})
    return results

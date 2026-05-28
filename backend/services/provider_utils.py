import logging
from pathlib import Path
from config import get_settings

logger = logging.getLogger(__name__)

PROVIDERS_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"


def _load_yaml_config() -> dict:
    import yaml

    try:
        with open(PROVIDERS_YAML) as f:
            return yaml.safe_load(f)
    except Exception:
        return {"default_provider": "docling", "providers": []}


def has_provider_api_key(provider_name: str) -> bool:
    return bool(resolve_provider_api_key(provider_name).strip())


def resolve_provider_api_key(provider_name: str) -> str:
    """Resolve the API key to use for the requested provider."""
    settings = get_settings()

    if provider_name == "litellm":
        return settings.openrouter_api_key or settings.gemini_api_key or ""

    return getattr(settings, f"{provider_name}_api_key", "")


def choose_default_provider_model() -> tuple[str, str]:
    """Pick the first configured provider/model pair for internal inference tasks."""
    config = _load_yaml_config()
    for prov_cfg in config.get("providers", []):
        name = prov_cfg["name"]
        if name == "docling":
            continue
        models = prov_cfg.get("models", [])
        if models and has_provider_api_key(name):
            return (name, models[0]["id"])

    logger.warning(
        "No provider config found in YAML, falling back to hardcoded defaults"
    )
    if has_provider_api_key("gemini"):
        return ("gemini", "gemini-2.5-flash-lite")
    if has_provider_api_key("openrouter"):
        return ("openrouter", "qwen/qwen3.5-flash-02-23")
    if has_provider_api_key("litellm"):
        return ("litellm", "google/gemma-4-31b-it")

    raise ValueError("No provider API key configured")

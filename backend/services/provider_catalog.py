from pathlib import Path
import logging
import yaml

from config import get_settings
from services.gemini import GeminiProvider
from services.litellm_provider import LiteLLMProvider
from services.openrouter import OpenRouterProvider
from services import provider_utils

logger = logging.getLogger(__name__)

PROVIDERS_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"
PROVIDER_CLASSES = {
    "openrouter": OpenRouterProvider,
    "gemini": GeminiProvider,
    "litellm": LiteLLMProvider,
}
resolve_provider_api_key = provider_utils.resolve_provider_api_key


def load_providers_config() -> dict:
    try:
        with open(PROVIDERS_YAML) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load providers.yaml: %s", e)
        return {"default_provider": "docling", "providers": []}


def list_provider_catalog() -> list[dict]:
    settings = get_settings()
    config = load_providers_config()

    api_key_map = {
        "openrouter": bool(
            settings.openrouter_api_key and settings.openrouter_api_key.strip()
        ),
        "gemini": bool(settings.gemini_api_key and settings.gemini_api_key.strip()),
        "litellm": bool(provider_utils.resolve_provider_api_key("litellm").strip()),
    }

    providers: list[dict] = []
    for prov_cfg in config.get("providers", []):
        name = prov_cfg["name"]

        if name == "docling":
            continue

        providers.append(
            {
                "name": name,
                "display_name": prov_cfg.get("display_name", name),
                "models": prov_cfg.get("models", []),
                "has_api_key": api_key_map.get(name, False),
                "is_default": config.get("default_provider") == name,
            }
        )

    return providers


async def get_provider(provider_name: str, api_key: str):
    cls = PROVIDER_CLASSES.get(provider_name)
    if not cls:
        raise ValueError(f"Unknown provider: {provider_name}")
    return cls(api_key=api_key)


def create_provider(provider_name: str, api_key: str | None = None):
    cls = PROVIDER_CLASSES.get(provider_name)
    if not cls:
        raise ValueError(f"Unknown provider: {provider_name}")

    resolved_api_key = (
        api_key
        if api_key is not None
        else provider_utils.resolve_provider_api_key(provider_name)
    )
    if not resolved_api_key:
        raise ValueError(f"No API key configured for {provider_name}")

    return cls(api_key=resolved_api_key)


def _default_model(provider_name: str) -> str:
    config = load_providers_config()
    for prov in config.get("providers", []):
        if prov["name"] == provider_name:
            models = prov.get("models", [])
            if models:
                return models[0]["id"]
    return ""

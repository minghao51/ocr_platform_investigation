from pathlib import Path
import logging
import yaml

from config import get_settings
from services.provider_utils import resolve_provider_api_key

logger = logging.getLogger(__name__)

PROVIDERS_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"


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
        "openrouter": bool(settings.openrouter_api_key and settings.openrouter_api_key.strip()),
        "gemini": bool(settings.gemini_api_key and settings.gemini_api_key.strip()),
        "litellm": bool(resolve_provider_api_key("litellm").strip()),
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

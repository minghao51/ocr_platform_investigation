from fastapi import APIRouter
from pathlib import Path
import yaml
import logging

from config import get_settings
from services.provider_utils import resolve_provider_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/providers", tags=["providers"])

PROVIDERS_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"


def _load_providers_config():
    try:
        with open(PROVIDERS_YAML) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Failed to load providers.yaml: {e}")
        return {"default_provider": "docling", "providers": []}


@router.get("/")
async def list_providers():
    """List all VLM providers and their models from config."""
    settings = get_settings()
    config = _load_providers_config()

    api_key_map = {
        "openrouter": bool(settings.openrouter_api_key and settings.openrouter_api_key.strip()),
        "gemini": bool(settings.gemini_api_key and settings.gemini_api_key.strip()),
        "litellm": bool(resolve_provider_api_key("litellm").strip()),
    }

    providers = []
    for prov_cfg in config.get("providers", []):
        name = prov_cfg["name"]

        if name == "docling":
            continue

        has_key = api_key_map.get(name, False)
        models = prov_cfg.get("models", [])

        providers.append({
            "name": name,
            "display_name": prov_cfg.get("display_name", name),
            "models": models,
            "has_api_key": has_key,
            "is_default": config.get("default_provider") == name,
        })

    return providers

from fastapi import APIRouter
from pathlib import Path
import yaml
import logging

from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.litellm_provider import LiteLLMProvider
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

    runtime_models = {}
    if api_key_map.get("openrouter"):
        try:
            runtime_models["openrouter"] = OpenRouterProvider(settings.openrouter_api_key).get_models()
        except Exception:
            pass
    if api_key_map.get("gemini"):
        try:
            runtime_models["gemini"] = GeminiProvider(settings.gemini_api_key).get_models()
        except Exception:
            pass
    if api_key_map.get("litellm"):
        try:
            runtime_models["litellm"] = LiteLLMProvider(resolve_provider_api_key("litellm")).get_models()
        except Exception:
            pass

    providers = []
    for prov_cfg in config.get("providers", []):
        name = prov_cfg["name"]

        # Docling is a processing method, not a cloud provider selection.
        if name == "docling":
            continue

        has_key = api_key_map.get(name, False)
        yaml_models = prov_cfg.get("models", [])
        models = yaml_models if yaml_models else runtime_models.get(name, [])

        providers.append({
            "name": name,
            "display_name": prov_cfg.get("display_name", name),
            "models": models,
            "has_api_key": has_key,
            "is_default": config.get("default_provider") == name,
        })

    return providers

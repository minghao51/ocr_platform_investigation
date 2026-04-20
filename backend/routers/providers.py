from fastapi import APIRouter
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.litellm_provider import LiteLLMProvider
from config import get_settings
from services.provider_utils import resolve_provider_api_key

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/")
async def list_providers():
    """List all VLM providers and their models, including those without API keys"""
    settings = get_settings()

    providers = []

    # OpenRouter
    openrouter_has_key = bool(
        settings.openrouter_api_key and settings.openrouter_api_key.strip()
    )
    openrouter_models = []
    if openrouter_has_key:
        try:
            openrouter = OpenRouterProvider(settings.openrouter_api_key)
            openrouter_models = openrouter.get_models()
        except Exception as e:
            print(f"Error loading OpenRouter models: {e}")
    providers.append(
        {
            "name": "openrouter",
            "display_name": "OpenRouter",
            "models": openrouter_models,
            "has_api_key": openrouter_has_key,
        }
    )

    # Gemini
    gemini_has_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip())
    gemini_models = []
    if gemini_has_key:
        try:
            gemini = GeminiProvider(settings.gemini_api_key)
            gemini_models = gemini.get_models()
        except Exception as e:
            print(f"Error loading Gemini models: {e}")
    providers.append(
        {
            "name": "gemini",
            "display_name": "Google Gemini",
            "models": gemini_models,
            "has_api_key": gemini_has_key,
        }
    )

    # LiteLLM (unified provider - uses OPENROUTER_API_KEY or any configured key)
    litellm_api_key = resolve_provider_api_key("litellm")
    litellm_has_key = bool(litellm_api_key.strip())
    litellm_models = []
    if litellm_has_key:
        try:
            litellm_prov = LiteLLMProvider(litellm_api_key)
            litellm_models = litellm_prov.get_models()
        except Exception as e:
            print(f"Error loading LiteLLM models: {e}")
    providers.append(
        {
            "name": "litellm",
            "display_name": "LiteLLM (Unified)",
            "models": litellm_models,
            "has_api_key": litellm_has_key,
        }
    )

    return providers

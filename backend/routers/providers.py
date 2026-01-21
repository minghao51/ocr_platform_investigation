from fastapi import APIRouter
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from config import get_settings

router = APIRouter(prefix="/api/providers", tags=["providers"])

@router.get("/")
async def list_providers():
    """List all VLM providers and their models, including those without API keys"""
    settings = get_settings()

    providers = []

    # Nebius
    nebius_has_key = bool(settings.nebius_api_key and settings.nebius_api_key.strip())
    nebius_models = []
    if nebius_has_key:
        try:
            nebius = NebiusProvider(settings.nebius_api_key)
            nebius_models = nebius.get_models()
        except Exception as e:
            print(f"Error loading Nebius models: {e}")
    providers.append({
        "name": "nebius",
        "display_name": "Nebius",
        "models": nebius_models,
        "has_api_key": nebius_has_key
    })

    # OpenRouter
    openrouter_has_key = bool(settings.openrouter_api_key and settings.openrouter_api_key.strip())
    openrouter_models = []
    if openrouter_has_key:
        try:
            openrouter = OpenRouterProvider(settings.openrouter_api_key)
            openrouter_models = openrouter.get_models()
        except Exception as e:
            print(f"Error loading OpenRouter models: {e}")
    providers.append({
        "name": "openrouter",
        "display_name": "OpenRouter",
        "models": openrouter_models,
        "has_api_key": openrouter_has_key
    })

    # Gemini
    gemini_has_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip())
    gemini_models = []
    if gemini_has_key:
        try:
            gemini = GeminiProvider(settings.gemini_api_key)
            gemini_models = gemini.get_models()
        except Exception as e:
            print(f"Error loading Gemini models: {e}")
    providers.append({
        "name": "gemini",
        "display_name": "Google Gemini",
        "models": gemini_models,
        "has_api_key": gemini_has_key
    })

    return providers

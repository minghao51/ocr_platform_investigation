from fastapi import APIRouter
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from config import get_settings

router = APIRouter(prefix="/api/providers", tags=["providers"])

@router.get("/")
async def list_providers():
    """List all available VLM providers and their models"""
    settings = get_settings()
    
    providers = []
    
    # Nebius
    if settings.nebius_api_key:
        try:
            nebius_models = NebiusProvider.get_models()
            providers.append({
                "name": "nebius",
                "display_name": "Nebius",
                "models": nebius_models
            })
        except Exception:
            pass
    
    # OpenRouter
    if settings.openrouter_api_key:
        try:
            openrouter_models = OpenRouterProvider.get_models()
            providers.append({
                "name": "openrouter",
                "display_name": "OpenRouter",
                "models": openrouter_models
            })
        except Exception:
            pass
    
    # Gemini
    if settings.gemini_api_key:
        try:
            gemini_models = GeminiProvider.get_models()
            providers.append({
                "name": "gemini",
                "display_name": "Google Gemini",
                "models": gemini_models
            })
        except Exception:
            pass
    
    return providers

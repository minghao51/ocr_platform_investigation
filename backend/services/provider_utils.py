from config import get_settings


def has_provider_api_key(provider_name: str) -> bool:
    return bool(resolve_provider_api_key(provider_name).strip())


def resolve_provider_api_key(provider_name: str) -> str:
    """Resolve the API key to use for the requested provider."""
    settings = get_settings()

    if provider_name == "litellm":
        return (
            settings.openrouter_api_key
            or settings.gemini_api_key
            or ""
        )

    return getattr(settings, f"{provider_name}_api_key", "")


def choose_default_provider_model() -> tuple[str, str]:
    """Pick the first configured provider/model pair for internal inference tasks."""
    if has_provider_api_key("gemini"):
        return ("gemini", "gemini-2.5-flash-lite")
    if has_provider_api_key("openrouter"):
        return ("openrouter", "qwen/qwen3.5-flash-02-23")
    if has_provider_api_key("litellm"):
        return ("litellm", "google/gemma-4-31b-it")

    raise ValueError("No provider API key configured")

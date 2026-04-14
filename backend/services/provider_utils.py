from config import get_settings


def choose_default_provider_model() -> tuple[str, str]:
    """Pick the first configured provider/model pair for internal inference tasks."""
    settings = get_settings()

    if settings.gemini_api_key:
        return ("gemini", "gemini-2.5-flash")
    if settings.openrouter_api_key:
        return ("openrouter", "qwen/qwen3.6-plus:free")
    if settings.nebius_api_key:
        return ("nebius", "Qwen/Qwen2.5-VL-72B-Instruct")

    raise ValueError("No provider API key configured")

import pytest
from unittest.mock import patch, MagicMock


class TestProviderCatalog:
    def test_provider_classes_defined(self):
        from services.provider_catalog import PROVIDER_CLASSES

        assert "openrouter" in PROVIDER_CLASSES
        assert "gemini" in PROVIDER_CLASSES
        assert "litellm" in PROVIDER_CLASSES

    @pytest.mark.asyncio
    async def test_get_provider_known(self):
        from services.provider_catalog import get_provider

        provider = await get_provider("openrouter", "test-key")
        assert provider is not None

    @pytest.mark.asyncio
    async def test_get_provider_unknown_raises(self):
        from services.provider_catalog import get_provider

        with pytest.raises(ValueError, match="Unknown provider"):
            await get_provider("nonexistent", "key")

    def test_load_providers_config_fallback(self):
        from services.provider_catalog import load_providers_config

        with patch("builtins.open", MagicMock(side_effect=FileNotFoundError)):
            config = load_providers_config()
            assert config == {"default_provider": "docling", "providers": []}

    def test_default_model_returns_empty_for_unknown(self):
        from services.provider_catalog import _default_model

        model = _default_model("nonexistent_provider")
        assert model == ""

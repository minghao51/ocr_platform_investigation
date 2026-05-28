from typing import Dict, Any, Optional
from PIL import Image
import json
import litellm
from .vlm_provider import VLMProvider, ExtractionResult, TokenUsage


class LiteLLMProvider(VLMProvider):
    """
    Unified VLM provider powered by LiteLLM.

    Provides access to models NOT covered by the dedicated Gemini/OpenRouter
    providers.  Supports 140+ backends through litellm prefixes:
        - openrouter/google/gemma-4-31b-it
        - openrouter/meta-llama/llama-4-scout-17b-16e
        - Any litellm-compatible model string
    """

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "openrouter/google/gemma-4-31b-it",
        **kwargs,
    ) -> ExtractionResult:
        litellm_model = self._resolve_model(model)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                        },
                    },
                ],
            }
        ]

        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            response = await self._call_litellm(
                litellm_model,
                messages,
                schema,
                kwargs,
            )

            content = response.choices[0].message.content

            return ExtractionResult(
                raw_response=response.model_dump()
                if hasattr(response, "model_dump")
                else None,
                content=content,
                usage=TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                model=model,
            )
        except Exception:
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Optional[Dict[str, Any]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ExtractionResult:
        litellm_model = self._resolve_model(model)

        system_prompt_override = kwargs.pop("system_prompt", None)

        if schema_definition is None:
            system_prompt = system_prompt_override or (
                "You are a document transcription assistant. "
                "Return only clean Markdown with no JSON wrapper."
            )
        else:
            system_prompt = system_prompt_override or (
                "You are a document data extraction assistant. "
                "Extract information from the following text according to the provided schema. "
                "Return ONLY valid JSON. No explanations, no markdown formatting."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ""},
        ]

        user_content = f"{prompt}\n\nDocument text:\n{text}"
        if schema_definition is not None:
            user_content += (
                f"\n\nTarget JSON schema:\n{json.dumps(schema_definition, indent=2)}"
            )
        messages[1]["content"] = user_content

        try:
            request_kwargs = {
                "model": litellm_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_key": self.api_key if self.api_key != "litellm-no-key" else None,
            }
            if schema_definition is not None:
                request_kwargs["response_format"] = {"type": "json_object"}

            response = await litellm.acompletion(**request_kwargs)

            content = response.choices[0].message.content

            return ExtractionResult(
                content=content,
                model=model,
                usage=TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
            )

        except Exception:
            return ExtractionResult(
                error="Provider request failed", success=False, model=model
            )

    async def _call_litellm(
        self,
        model: str,
        messages: list,
        schema: Dict[str, Any],
        kwargs: Dict[str, Any],
    ) -> Any:
        json_schema = {
            "name": "extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
                "additionalProperties": False,
            },
        }

        api_key = self.api_key if self.api_key != "litellm-no-key" else None

        try:
            return await litellm.acompletion(
                model=model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": json_schema,
                },
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 4096),
                api_key=api_key,
            )
        except Exception:
            return await litellm.acompletion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 4096),
                api_key=api_key,
            )

    @staticmethod
    def _resolve_model(model: str) -> str:
        if "/" in model and not model.startswith(
            ("openrouter/", "gemini/", "openai/", "anthropic/")
        ):
            return f"openrouter/{model}"
        return model

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)

from typing import Dict, Any, Optional
from PIL import Image
import json
import litellm
from .vlm_provider import VLMProvider


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
    ) -> Dict[str, Any]:
        litellm_model = self._resolve_model(model)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}",
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

        try:
            response = await self._call_litellm(
                litellm_model,
                messages,
                schema,
                kwargs,
            )

            content = response.choices[0].message.content

            return {
                "raw_response": response.model_dump(),
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }
        except Exception as e:
            return {"error": str(e), "content": None, "model": model}

    async def process_text(
        self,
        text: str,
        prompt: str,
        schema_definition: Optional[Dict[str, Any]],
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs,
    ) -> Dict[str, Any]:
        litellm_model = self._resolve_model(model)

        if schema_definition is None:
            system_prompt = (
                "You are a document transcription assistant. "
                "Return only clean Markdown with no JSON wrapper."
            )
        else:
            system_prompt = (
                "You are a document data extraction assistant. "
                "Extract information from the following text according to this JSON schema:\n\n"
                f"{json.dumps(schema_definition, indent=2)}\n\n"
                "Return ONLY valid JSON. No explanations, no markdown formatting."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{prompt}\n\nDocument text:\n{text}",
            },
        ]

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

            return {
                "content": content,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            return {"error": str(e), "content": None, "model": model}

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
        if "/" in model and not model.startswith(("openrouter/", "gemini/", "openai/", "anthropic/")):
            return f"openrouter/{model}"
        return model

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)

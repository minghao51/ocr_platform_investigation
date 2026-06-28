from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal, List

from extraction_methods import EXTRACTION_METHODS_WITH_AUTO


MAX_PROMPT_LENGTH = 10_000
MAX_SCHEMA_DEPTH = 8
MAX_SCHEMA_KEYS = 200
MAX_TOKENS_LIMIT = 128_000
PROCESSING_DEFAULT_TEMPERATURE = 0.1
PROCESSING_DEFAULT_MAX_TOKENS = 8192
PROCESSING_DEFAULT_QUALITY_THRESHOLD = 40.0


def _count_schema_keys(value: Any, depth: int = 0) -> int:
    """Recursively count keys in a schema dict and validate depth."""
    if depth > MAX_SCHEMA_DEPTH:
        raise ValueError(
            f"Schema definition exceeds maximum nesting depth of {MAX_SCHEMA_DEPTH}"
        )
    if isinstance(value, dict):
        return sum(1 + _count_schema_keys(v, depth + 1) for v in value.values())
    if isinstance(value, list):
        return sum(_count_schema_keys(item, depth + 1) for item in value)
    return 0


class ProcessRequest(BaseModel):
    file_id: str
    provider: Optional[str] = None
    model: Optional[str] = None
    schema_id: Optional[int] = None
    schema_definition: Optional[Dict[str, Any]] = None
    schema_mode: Optional[Literal["raw", "auto-detect", "manual"]] = "auto-detect"
    extraction_method: Optional[Literal[*EXTRACTION_METHODS_WITH_AUTO]] = "auto"
    prompt: Optional[str] = Field(
        default="Extract all information from this document",
        max_length=MAX_PROMPT_LENGTH,
    )
    temperature: Optional[float] = Field(
        default=PROCESSING_DEFAULT_TEMPERATURE, ge=0.0, le=2.0
    )
    max_tokens: Optional[int] = Field(
        default=PROCESSING_DEFAULT_MAX_TOKENS, ge=1, le=MAX_TOKENS_LIMIT
    )
    # Quality gate options
    quality_threshold: Optional[float] = Field(
        default=PROCESSING_DEFAULT_QUALITY_THRESHOLD, ge=0.0, le=100.0
    )
    auto_preprocess: Optional[bool] = True  # Auto-fix quality issues before VLM
    skip_quality: Optional[bool] = False  # Bypass quality gate entirely

    @field_validator("prompt")
    @classmethod
    def validate_prompt_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
            )
        return v

    @field_validator("schema_definition")
    @classmethod
    def validate_schema_definition(
        cls, v: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        key_count = _count_schema_keys(v)
        if key_count > MAX_SCHEMA_KEYS:
            raise ValueError(
                f"Schema definition contains too many keys ({key_count}). "
                f"Maximum allowed is {MAX_SCHEMA_KEYS}."
            )
        return v


class ProcessResponse(BaseModel):
    job_id: int
    status: str
    guest_token: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SchemaSuggestRequest(BaseModel):
    file_ids: List[str] = Field(min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None


class JobCorrectionRequest(BaseModel):
    corrected_result: Dict[str, Any]
    feedback_tags: List[
        Literal["wrong_field", "missed_field", "bad_type", "layout_issue"]
    ] = Field(default_factory=list)
    notes: Optional[str] = None

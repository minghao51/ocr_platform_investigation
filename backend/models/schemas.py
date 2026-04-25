from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List


class ProcessRequest(BaseModel):
    file_id: str
    provider: Optional[str] = None
    model: Optional[str] = None
    schema_id: Optional[int] = None
    schema_definition: Optional[Dict[str, Any]] = None
    schema_mode: Optional[
        Literal["raw", "auto-detect", "manual"]
    ] = "auto-detect"
    extraction_method: Optional[
        Literal[
            "auto",
            "text",
            "vision",
            "hybrid",
            "docling-parse",
            "docling-extract",
            "transcription",
        ]
    ] = "auto"
    prompt: Optional[str] = "Extract all information from this document"
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 8192
    # Quality gate options
    quality_threshold: Optional[float] = (
        40.0  # Minimum quality score to proceed (0-100)
    )
    auto_preprocess: Optional[bool] = True  # Auto-fix quality issues before VLM
    skip_quality: Optional[bool] = False  # Bypass quality gate entirely


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
    ] = []
    notes: Optional[str] = None

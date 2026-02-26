from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal


class ProcessRequest(BaseModel):
    file_id: str
    provider: str  # 'nebius', 'openrouter', 'gemini'
    model: str
    schema_id: Optional[int] = None
    schema_definition: Optional[Dict[str, Any]] = None
    extraction_method: Optional[Literal["auto", "text", "vision", "hybrid"]] = "auto"
    prompt: Optional[str] = "Extract all information from this document"
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 4096


class ProcessResponse(BaseModel):
    job_id: int
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

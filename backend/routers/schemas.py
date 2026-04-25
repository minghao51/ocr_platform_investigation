from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from database import crud
from services.schema_service import SchemaService
from services.schema_suggester import SchemaSuggestionService
from services.provider_utils import (
    choose_default_provider_model,
    has_provider_api_key,
)
from dependencies import get_optional_user, get_current_user
from routers.shared import ensure_file_access
from models.schemas import SchemaSuggestRequest
from config import get_settings
import json

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

PROVIDERS_YAML = Path(__file__).parent.parent / "config" / "providers.yaml"


def _load_providers_config():
    try:
        with open(PROVIDERS_YAML) as f:
            return yaml.safe_load(f)
    except Exception:
        return {}


def _get_schema_suggestion_config():
    config = _load_providers_config()
    suggestion_cfg = config.get("schema_suggestion", {})
    return suggestion_cfg.get("provider"), suggestion_cfg.get("model")


def _resolve_schema_suggestion_target(
    payload: SchemaSuggestRequest,
) -> tuple[str, str]:
    config_provider, config_model = _get_schema_suggestion_config()
    candidates = [
        (config_provider, config_model),
        (payload.provider, payload.model),
    ]

    for provider_name, model in candidates:
        if provider_name and model and has_provider_api_key(provider_name):
            return provider_name, model

    try:
        return choose_default_provider_model()
    except ValueError:
        for provider_name, model in candidates:
            if provider_name and model:
                return provider_name, model
        raise


class SchemaCreate(BaseModel):
    name: str
    definition: Dict[str, Any]
    description: Optional[str] = None


class SchemaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    definition: Dict[str, Any]
    is_template: bool
    created_at: str
    updated_at: str


@router.get("/")
async def list_schemas(is_template: Optional[bool] = None):
    """List all schemas"""
    schemas = await crud.list_schemas(is_template=is_template)
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "definition": json.loads(s["definition"]),
            "is_template": bool(s["is_template"]),
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
        }
        for s in schemas
    ]


@router.post("/")
async def create_schema(schema: SchemaCreate):
    """Create a new schema"""
    try:
        schema_id = await crud.create_schema(
            name=schema.name,
            definition=schema.definition,
            description=schema.description,
            is_template=False,
        )
        created = await crud.get_schema(schema_id)
        return {
            "id": created["id"],
            "name": created["name"],
            "description": created["description"],
            "definition": json.loads(created["definition"]),
            "is_template": bool(created["is_template"]),
            "created_at": created["created_at"],
            "updated_at": created["updated_at"],
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Schema name already exists")
        raise


@router.get("/templates")
async def get_templates():
    """Get built-in schema templates"""
    templates = SchemaService.get_builtin_templates()
    return [
        {
            "name": name,
            "definition": definition,
            "is_template": True,
            "description": f"Built-in {name} template",
        }
        for name, definition in templates.items()
    ]


@router.post("/suggestions")
async def suggest_schema(
    payload: SchemaSuggestRequest,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    settings = get_settings()
    provider_name, model = _resolve_schema_suggestion_target(payload)
    api_key = getattr(settings, f"{provider_name}_api_key", "")

    file_records = []
    guest_token = request.headers.get("X-Guest-Token")
    for file_id in payload.file_ids:
        file_record = await crud.get_uploaded_file(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
        ensure_file_access(file_record, current_user, guest_token)
        file_records.append(file_record)

    suggester = SchemaSuggestionService()
    try:
        suggestion = await suggester.suggest_schema(
            file_records=file_records,
            provider_name=provider_name,
            model=model,
            api_key=api_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to generate schema suggestion: {exc}"
        ) from exc

    created_by_user_id = current_user.get("user_id") if current_user else None
    suggestion_id = await crud.create_schema_suggestion(
        file_ids=payload.file_ids,
        provider=suggestion["provider"],
        model=suggestion["model"],
        document_type=suggestion["document_type"],
        draft_name=suggestion["draft_name"],
        schema_definition=suggestion["schema_definition"],
        field_descriptions=suggestion["field_descriptions"],
        rationale=suggestion["rationale"],
        confidence=suggestion["confidence"],
        created_by_user_id=created_by_user_id,
    )
    stored = await crud.get_schema_suggestion(suggestion_id)
    return stored


@router.get("/suggestions/list")
async def list_schema_suggestion_history(
    current_user: dict = Depends(get_current_user),
):
    user_id = None if current_user.get("is_admin", False) else current_user.get("user_id")
    return await crud.list_schema_suggestions(created_by_user_id=user_id)


@router.get("/{schema_id}")
async def get_schema(schema_id: int):
    """Get schema by ID"""
    schema = await crud.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return {
        "id": schema["id"],
        "name": schema["name"],
        "description": schema["description"],
        "definition": json.loads(schema["definition"]),
        "is_template": bool(schema["is_template"]),
        "created_at": schema["created_at"],
        "updated_at": schema["updated_at"],
    }

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import crud
from services.schema_service import SchemaService
import json

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

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
            "updated_at": s["updated_at"]
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
            is_template=False
        )
        created = await crud.get_schema(schema_id)
        return {
            "id": created["id"],
            "name": created["name"],
            "description": created["description"],
            "definition": json.loads(created["definition"]),
            "is_template": bool(created["is_template"]),
            "created_at": created["created_at"],
            "updated_at": created["updated_at"]
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
            "description": f"Built-in {name} template"
        }
        for name, definition in templates.items()
    ]

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
        "updated_at": schema["updated_at"]
    }

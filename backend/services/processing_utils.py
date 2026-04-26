import json
import logging
from typing import Dict, Any, Optional

from database import crud
from services.schema_service import SchemaService

logger = logging.getLogger(__name__)


def parse_and_validate_response(
    content: str,
    schema_definition: Dict[str, Any],
    schema_service: Optional[SchemaService] = None,
) -> Dict[str, Any]:
    if schema_service is None:
        schema_service = SchemaService()

    try:
        data = json.loads(content)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass

        is_valid, validated_data, error = schema_service.validate_data(
            data, schema_definition
        )

        if is_valid:
            return {"success": True, "data": validated_data}
        else:
            return {"success": False, "error": f"Validation failed: {error}"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON response: {str(e)}"}


async def update_job_status_with_broadcast(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
    usage: Optional[Dict[str, Any]] = None,
):
    job = await crud.update_job_status(
        job_id,
        status,
        result=result,
        error_message=error_message,
        processing_time=processing_time,
        usage=usage,
    )

    if job:
        try:
            from routers.websocket import broadcast_job_update

            await broadcast_job_update(job_id, job)
        except Exception as e:
            logger.warning(f"Failed to broadcast job update via WebSocket: {e}")

    return job

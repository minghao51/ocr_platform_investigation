import aiosqlite
import json
from typing import Optional, List, Dict, Any
from database.pool import connect
from database.crud._shared import loads_if_json


def _deserialize_suggestion(row: dict) -> dict:
    for key in ("file_ids", "schema_definition", "field_descriptions"):
        row[key] = loads_if_json(row.get(key)) or ([] if key == "file_ids" else {})
    return row


async def create_schema(
    name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None,
    is_template: bool = False,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """INSERT INTO schemas (name, description, definition, is_template)
               VALUES (?, ?, ?, ?)""",
            (name, description, json.dumps(definition), is_template),
        )
        await db.commit()
        return cursor.lastrowid


async def get_schema(schema_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM schemas WHERE id = ?", (schema_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def list_schemas(is_template: Optional[bool] = None) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row

        if is_template is not None:
            cursor = await db.execute(
                "SELECT * FROM schemas WHERE is_template = ? ORDER BY name",
                (is_template,),
            )
        else:
            cursor = await db.execute("SELECT * FROM schemas ORDER BY name")

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def create_schema_suggestion(
    file_ids: List[str],
    provider: str,
    model: str,
    schema_definition: Dict[str, Any],
    field_descriptions: Dict[str, str],
    rationale: str,
    confidence: float,
    document_type: Optional[str] = None,
    draft_name: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
) -> int:
    async with connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO schema_suggestions (
                file_ids, provider, model, document_type, draft_name,
                schema_definition, field_descriptions, rationale, confidence, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(file_ids),
                provider,
                model,
                document_type,
                draft_name,
                json.dumps(schema_definition),
                json.dumps(field_descriptions),
                rationale,
                confidence,
                created_by_user_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_schema_suggestion(suggestion_id: int) -> Optional[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM schema_suggestions WHERE id = ?", (suggestion_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return _deserialize_suggestion(dict(row))


async def list_schema_suggestions(
    created_by_user_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        if created_by_user_id is None:
            cursor = await db.execute(
                "SELECT * FROM schema_suggestions ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM schema_suggestions WHERE created_by_user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (created_by_user_id, limit, offset),
            )
        rows = await cursor.fetchall()
        return [_deserialize_suggestion(dict(row)) for row in rows]


async def create_job_correction(
    job_id: int,
    original_result: Dict[str, Any],
    corrected_result: Dict[str, Any],
    diff_summary: List[Dict[str, Any]],
    feedback_tags: List[str],
    reviewer_user_id: Optional[int],
    notes: Optional[str] = None,
) -> int:
    async with connect() as db:
        await db.execute("BEGIN IMMEDIATE")
        try:
            cursor = await db.execute(
                """
                INSERT INTO job_corrections (
                    job_id, original_result, corrected_result, diff_summary,
                    feedback_tags, notes, reviewer_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    json.dumps(original_result),
                    json.dumps(corrected_result),
                    json.dumps(diff_summary),
                    json.dumps(feedback_tags),
                    notes,
                    reviewer_user_id,
                ),
            )
            await db.execute(
                "UPDATE processing_jobs SET correction_status = ? WHERE id = ?",
                ("corrected", job_id),
            )
            await db.commit()
            return cursor.lastrowid
        except Exception:
            await db.rollback()
            raise


async def list_job_corrections(job_id: int) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT jc.*, u.username AS reviewer_username
            FROM job_corrections jc
            LEFT JOIN users u ON u.id = jc.reviewer_user_id
            WHERE jc.job_id = ?
            ORDER BY jc.created_at DESC
            """,
            (job_id,),
        )
        rows = await cursor.fetchall()
        corrections = []
        for row in rows:
            item = dict(row)
            for key in (
                "original_result",
                "corrected_result",
                "diff_summary",
                "feedback_tags",
            ):
                item[key] = loads_if_json(item.get(key))
            corrections.append(item)
        return corrections


async def get_latest_job_correction(job_id: int) -> Optional[Dict[str, Any]]:
    corrections = await list_job_corrections(job_id)
    return corrections[0] if corrections else None


async def upsert_prompt_learning_entry(
    schema_name: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    processing_method: Optional[str],
    entry_type: str,
    content: str,
    source_correction_count: int,
    last_correction_id: int,
) -> int:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        await db.execute("BEGIN IMMEDIATE")
        try:
            cursor = await db.execute(
                """
                SELECT id FROM prompt_learning_entries
                WHERE COALESCE(schema_name, '') = COALESCE(?, '')
                  AND COALESCE(provider, '') = COALESCE(?, '')
                  AND COALESCE(model, '') = COALESCE(?, '')
                  AND COALESCE(processing_method, '') = COALESCE(?, '')
                  AND entry_type = ?
                """,
                (schema_name, provider, model, processing_method, entry_type),
            )
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    """
                    UPDATE prompt_learning_entries
                    SET content = ?, source_correction_count = ?, last_correction_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (content, source_correction_count, last_correction_id, row["id"]),
                )
                await db.commit()
                return row["id"]

            cursor = await db.execute(
                """
                INSERT INTO prompt_learning_entries (
                    schema_name, provider, model, processing_method,
                    entry_type, content, source_correction_count, last_correction_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schema_name,
                    provider,
                    model,
                    processing_method,
                    entry_type,
                    content,
                    source_correction_count,
                    last_correction_id,
                ),
            )
            await db.commit()
            return cursor.lastrowid
        except Exception:
            await db.rollback()
            raise


async def list_prompt_learning_entries(
    schema_name: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    processing_method: Optional[str] = None,
) -> List[Dict[str, Any]]:
    async with connect() as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM prompt_learning_entries WHERE 1=1"
        params: List[Any] = []
        if schema_name:
            query += " AND schema_name = ?"
            params.append(schema_name)
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if model:
            query += " AND model = ?"
            params.append(model)
        if processing_method:
            query += " AND processing_method = ?"
            params.append(processing_method)
        query += " ORDER BY updated_at DESC"
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

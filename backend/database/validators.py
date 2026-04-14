"""
Column whitelist validators to prevent SQL injection in dynamic SQL operations.
"""

from typing import Set


# Whitelist of allowed column names for processing_jobs UPDATE operations
ALLOWED_JOB_UPDATE_COLUMNS: Set[str] = {
    "status",
    "result",
    "error_message",
    "processing_time_seconds",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost",
    "completed_at",
    "correction_status",
    "metadata",
    "quality_score",
    "quality_checks",
    "preprocessing_applied",
}


def validate_update_columns(columns: set[str]) -> None:
    """
    Validate that all column names are whitelisted before SQL interpolation.

    Args:
        columns: Set of column names to validate

    Raises:
        ValueError: If any column name is not in the whitelist
    """
    invalid = columns - ALLOWED_JOB_UPDATE_COLUMNS
    if invalid:
        raise ValueError(f"Invalid column names: {invalid}")

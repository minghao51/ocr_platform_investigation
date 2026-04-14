from collections import Counter
from typing import Any, Dict, List

from database import crud


class PromptLearningService:
    """Aggregate accepted corrections into reusable prompt/routing hints."""

    @staticmethod
    def summarize_diff(diff_summary: List[Dict[str, Any]]) -> str:
        if not diff_summary:
            return "No field-level changes captured."
        parts = []
        for item in diff_summary[:10]:
            path = item.get("path", "unknown")
            change_type = item.get("change_type", "updated")
            parts.append(f"{path}: {change_type}")
        return "; ".join(parts)

    async def update_from_correction(
        self,
        job: Dict[str, Any],
        correction_id: int,
        diff_summary: List[Dict[str, Any]],
        feedback_tags: List[str],
    ) -> None:
        existing_entries = await crud.list_prompt_learning_entries(
            schema_name=job.get("schema_name"),
            provider=job.get("provider"),
            model=job.get("model"),
        )
        tags_counter = Counter(feedback_tags)
        guidance = (
            f"Frequent correction tags: {dict(tags_counter)}. "
            f"Recent field changes: {self.summarize_diff(diff_summary)}"
        )
        source_count = 1
        for entry in existing_entries:
            if entry["entry_type"] == "prompt_hint":
                source_count = max(
                    source_count, (entry.get("source_correction_count") or 0) + 1
                )
                break

        await crud.upsert_prompt_learning_entry(
            schema_name=job.get("schema_name"),
            provider=job.get("provider"),
            model=job.get("model"),
            processing_method=job.get("processing_method"),
            entry_type="prompt_hint",
            content=guidance,
            source_correction_count=source_count,
            last_correction_id=correction_id,
        )

        if feedback_tags:
            await crud.upsert_prompt_learning_entry(
                schema_name=job.get("schema_name"),
                provider=job.get("provider"),
                model=job.get("model"),
                processing_method=job.get("processing_method"),
                entry_type="routing_note",
                content=(
                    "Observed correction tags suggest these failure modes: "
                    + ", ".join(sorted(set(feedback_tags)))
                ),
                source_correction_count=source_count,
                last_correction_id=correction_id,
            )

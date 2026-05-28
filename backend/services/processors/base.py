from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class Processor(ABC):
    MAX_FILE_SIZE = 50 * 1024 * 1024

    @abstractmethod
    async def process(
        self,
        job_id: Optional[int],
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Optional[Dict[str, Any]],
        prompt: str,
        **kwargs,
    ) -> Dict[str, Any]: ...

    def _validate_file_size(self, file_path: str) -> None:
        from config import get_settings

        max_size = get_settings().max_file_size
        size = Path(file_path).stat().st_size
        if size > max_size:
            raise ValueError(
                f"File too large ({size / 1024 / 1024:.1f}MB). Max: {max_size / 1024 / 1024}MB"
            )

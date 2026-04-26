from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Processor(ABC):
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
    ) -> Dict[str, Any]:
        ...

import asyncio
import logging
import os
import socket
from typing import Any

from config import get_settings
from database import crud
from services.processing import run_processing_job, run_text_processing_job

logger = logging.getLogger(__name__)

_poll_interval_seconds = 1.0
_worker_task: asyncio.Task | None = None
_worker_stop_event: asyncio.Event | None = None
_worker_id = f"{socket.gethostname()}:{os.getpid()}"


def _should_start_worker() -> bool:
    # Tests rely on deterministic job states and should not run async queue workers.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return bool(getattr(get_settings(), "enable_job_worker", True))


async def _run_job(item: dict[str, Any]) -> None:
    job_id = int(item["job_id"])
    task_type = item.get("task_type")
    file_path = item.get("file_path")
    payload = item.get("payload") or {}

    if task_type == "text":
        await run_text_processing_job(job_id, file_path, **payload)
        return

    if task_type == "processing":
        await run_processing_job(job_id, file_path, **payload)
        return

    raise ValueError(f"Unknown queue task type: {task_type}")


async def _worker_loop(stop_event: asyncio.Event) -> None:
    logger.info("Job queue worker started (%s)", _worker_id)
    while not stop_event.is_set():
        try:
            item = await crud.claim_next_queued_job(_worker_id)
            if not item:
                await asyncio.sleep(_poll_interval_seconds)
                continue

            job_id = int(item["job_id"])
            try:
                await _run_job(item)
                await crud.mark_queue_job_completed(job_id)
            except Exception as exc:
                logger.exception("Queue worker failed job %s: %s", job_id, exc)
                await crud.mark_queue_job_failed(job_id, f"{type(exc).__name__}: {exc}")
                await crud.update_job_status(
                    job_id,
                    "error",
                    error_message=f"Queue worker failed: {type(exc).__name__}: {exc}",
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Queue worker loop error: %s", exc)
            await asyncio.sleep(_poll_interval_seconds)

    logger.info("Job queue worker stopped (%s)", _worker_id)


async def start_job_worker() -> bool:
    """Start queue worker if enabled. Returns True when started."""
    global _worker_task, _worker_stop_event

    if not _should_start_worker():
        logger.info("Job queue worker disabled")
        return False

    if _worker_task and not _worker_task.done():
        return True

    _worker_stop_event = asyncio.Event()
    _worker_task = asyncio.create_task(_worker_loop(_worker_stop_event))
    return True


async def stop_job_worker() -> None:
    global _worker_task, _worker_stop_event

    if _worker_stop_event:
        _worker_stop_event.set()

    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass

    _worker_task = None
    _worker_stop_event = None


async def recover_queue_state() -> int:
    """Recover in-flight queue jobs after restart and return reset count."""
    return await crud.recover_inflight_queue_jobs()


async def enqueue_processing_task(
    job_id: int,
    file_path: str,
    payload: dict[str, Any],
    *,
    task_type: str = "processing",
) -> None:
    await crud.enqueue_job(
        job_id=job_id,
        task_type=task_type,
        file_path=file_path,
        payload=payload,
    )

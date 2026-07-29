from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from avicore.resource_manager import check_system_resources, get_optimal_worker_count


@dataclass
class TaskPlan:
    mode: str  # "sequential" or "parallel"
    worker_count: int
    reason: str


def schedule_batch_execution(files: list[Path], is_video: bool = False) -> TaskPlan:
    """Determine optimal execution mode and worker count based on media type and hardware status."""
    total_files = len(files)
    if total_files <= 1:
        return TaskPlan(mode="sequential", worker_count=1, reason="Single file execution")

    state = check_system_resources()
    if state.is_throttled:
        return TaskPlan(
            mode="sequential" if is_video else "parallel",
            worker_count=1 if is_video else 2,
            reason="High system memory pressure (>85%)",
        )

    workers = get_optimal_worker_count(is_video=is_video)
    if workers > 1:
        return TaskPlan(
            mode="parallel",
            worker_count=workers,
            reason=f"Parallel execution on {workers} workers ({'video' if is_video else 'image'} batch)",
        )

    return TaskPlan(mode="sequential", worker_count=1, reason="Sequential fallback")

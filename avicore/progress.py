from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class BatchProgressReport:
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    current_file: str = ""
    current_stage: str = "Initializing"
    elapsed_seconds: float = 0.0

    @property
    def percent_complete(self) -> float:
        if self.total_items == 0:
            return 100.0
        return round((self.completed_items + self.failed_items) / self.total_items * 100.0, 1)

    @property
    def eta_seconds(self) -> float:
        processed = self.completed_items + self.failed_items
        if processed == 0 or self.elapsed_seconds == 0:
            return 0.0
        rate = processed / self.elapsed_seconds
        remaining = self.total_items - processed
        return round(remaining / rate, 1)


ProgressCallback = Callable[[BatchProgressReport], None]

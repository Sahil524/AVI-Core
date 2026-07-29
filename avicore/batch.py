from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from avicore.progress import BatchProgressReport, ProgressCallback
from avicore.scheduler import schedule_batch_execution

logger = logging.getLogger("avicore.batch")


class BatchTaskCancelledException(Exception):
    pass


class BatchProcessor:
    """Manages parallel and sequential multi-file batch execution queues."""

    def __init__(self, progress_callback: ProgressCallback | None = None):
        self.progress_callback = progress_callback
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        """Signal cancellation to all active workers."""
        self.cancel_event.set()

    def run_batch(
        self,
        files: list[Path],
        worker_func: Callable[[Path], tuple[bool, str]],
        is_video: bool = False,
        retry_failures: bool = True,
    ) -> tuple[int, int, list[str]]:
        """Run batch tasks using the Intelligent Worker Scheduler."""
        if not files:
            return 0, 0, []

        plan = schedule_batch_execution(files, is_video=is_video)
        logger.info(
            f"Scheduling batch of {len(files)} files via {plan.mode} mode ({plan.worker_count} workers): {plan.reason}"
        )

        report = BatchProgressReport(total_items=len(files))
        start_time = time.time()

        success_count = 0
        failure_count = 0
        errors: list[str] = []
        lock = threading.Lock()

        def _execute_item_with_retry(item: Path) -> tuple[bool, str]:
            if self.cancel_event.is_set():
                return False, "Cancelled"

            ok, err = worker_func(item)
            if not ok and retry_failures and not self.cancel_event.is_set():
                logger.warning(f"Retrying failed item {item.name}...")
                time.sleep(0.2)
                ok, err = worker_func(item)

            return ok, err

        if plan.mode == "parallel" and plan.worker_count > 1:
            with ThreadPoolExecutor(max_workers=plan.worker_count) as executor:
                future_to_file = {executor.submit(_execute_item_with_retry, f): f for f in files}
                for future in as_completed(future_to_file):
                    if self.cancel_event.is_set():
                        break
                    f = future_to_file[future]
                    try:
                        ok, err = future.result()
                        with lock:
                            report.elapsed_seconds = time.time() - start_time
                            report.current_file = f.name
                            if ok:
                                success_count += 1
                                report.completed_items += 1
                            else:
                                failure_count += 1
                                report.failed_items += 1
                                errors.append(f"File: {f.name}\nReason: {err}")
                            if self.progress_callback:
                                self.progress_callback(report)
                    except Exception as exc:
                        with lock:
                            failure_count += 1
                            report.failed_items += 1
                            errors.append(f"File: {f.name}\nReason: {exc}")

        else:
            # Sequential execution mode
            for f in files:
                if self.cancel_event.is_set():
                    break
                ok, err = _execute_item_with_retry(f)
                report.elapsed_seconds = time.time() - start_time
                report.current_file = f.name
                if ok:
                    success_count += 1
                    report.completed_items += 1
                else:
                    failure_count += 1
                    report.failed_items += 1
                    errors.append(f"File: {f.name}\nReason: {err}")
                if self.progress_callback:
                    self.progress_callback(report)

        return success_count, failure_count, errors

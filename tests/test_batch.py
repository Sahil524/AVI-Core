from pathlib import Path

from avicore.batch import BatchProcessor
from avicore.progress import BatchProgressReport


def test_batch_processor_sequential():
    items = [Path("file1.mp4"), Path("file2.mp4"), Path("file3.mp4")]

    reports = []

    def progress_callback(report: BatchProgressReport):
        reports.append(report.completed_items + report.failed_items)

    def worker(item: Path) -> tuple[bool, str]:
        if item.name == "file2.mp4":
            return False, "Failed file2"
        return True, ""

    processor = BatchProcessor(progress_callback=progress_callback)

    # Mock scheduling to force sequential execution
    # We patch schedule_batch_execution to return sequential
    from unittest.mock import patch

    from avicore.scheduler import TaskPlan

    mock_plan = TaskPlan(mode="sequential", worker_count=1, reason="Test sequential")

    with patch("avicore.batch.schedule_batch_execution", return_value=mock_plan):
        success, failed, errors = processor.run_batch(items, worker, retry_failures=False)

        assert success == 2
        assert failed == 1
        assert len(errors) == 1
        assert "file2.mp4" in errors[0]
        # Should record progress updates
        assert len(reports) == 3
        assert reports == [1, 2, 3]


def test_batch_processor_parallel():
    items = [Path("file1.mp4"), Path("file2.mp4")]

    def worker(item: Path) -> tuple[bool, str]:
        return True, ""

    processor = BatchProcessor()

    from unittest.mock import patch

    from avicore.scheduler import TaskPlan

    mock_plan = TaskPlan(mode="parallel", worker_count=2, reason="Test parallel")

    with patch("avicore.batch.schedule_batch_execution", return_value=mock_plan):
        success, failed, errors = processor.run_batch(items, worker)

        assert success == 2
        assert failed == 0
        assert len(errors) == 0

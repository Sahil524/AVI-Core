from __future__ import annotations

import logging
import shutil
from pathlib import Path

from avicore.models import MediaInfo
from avicore.verifier import verify_output_file

logger = logging.getLogger("avicore.atomic")


def backup_original_safe(src: Path) -> Path:
    """Move source file safely into ./backup/ directory with cross-drive support."""
    backup_dir = src.parent / "backup"
    backup_dir.mkdir(exist_ok=True)

    target = backup_dir / src.name
    counter = 1
    while target.exists():
        target = backup_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    shutil.move(str(src), str(target))
    return target


def commit_two_phase_output(
    temp_output: Path,
    final_dst: Path,
    src: Path,
    src_info: MediaInfo,
    ffmpeg_path: Path,
    do_backup: bool = True,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Execute two-phase commit: Verify temp output -> Backup original -> Atomic move to final dst."""
    if dry_run:
        return True, ""

    # Phase 1: Verification
    valid, err_msg = verify_output_file(temp_output, src_info, ffmpeg_path)
    if not valid:
        try:
            if temp_output.exists():
                temp_output.unlink()
        except OSError as exc:
            logger.warning(f"Failed to unlink temp file {temp_output}: {exc}")
        return False, f"Verification failed: {err_msg}"

    # Phase 2: Transactional Commit
    try:
        if do_backup and src.exists() and src.resolve() != final_dst.resolve():
            backup_original_safe(src)

        # Cross-device safe atomic move
        shutil.move(str(temp_output), str(final_dst))
        return True, ""
    except Exception as exc:
        logger.exception(f"Atomic commit failed for {final_dst.name}: {exc}")
        try:
            if temp_output.exists():
                temp_output.unlink()
        except OSError:
            pass
        return False, f"Commit error: {exc}"

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from avicore.models import MediaInfo
from avicore.probe import probe_media_file

logger = logging.getLogger("avicore.verifier")


@dataclass
class VerificationReport:
    is_valid: bool
    error_message: str = ""
    resolution_match: bool = True
    stream_count_match: bool = True
    dst_info: MediaInfo | None = None
    details: dict[str, Any] = field(default_factory=dict)


def verify_output_file_detailed(
    dst_path: Path,
    src_info: MediaInfo,
    ffmpeg_path: Path,
    duration_tolerance_sec: float = 2.0,
) -> VerificationReport:
    """Verify output file existence, size, probe readability, stream presence, and duration parity."""
    if not dst_path.exists():
        return VerificationReport(is_valid=False, error_message=f"Output file does not exist: {dst_path.name}")

    file_size = dst_path.stat().st_size
    if file_size == 0:
        return VerificationReport(is_valid=False, error_message=f"Output file is 0 bytes: {dst_path.name}")

    try:
        dst_info = probe_media_file(dst_path, ffmpeg_path)
    except Exception as exc:
        return VerificationReport(is_valid=False, error_message=f"Output file failed media probing: {exc}")

    # Corrupted / No Stream Validation: if source expected video/audio, output must contain streams
    if (src_info.has_video or src_info.has_audio) and not dst_info.has_video and not dst_info.has_audio:
        return VerificationReport(
            is_valid=False,
            error_message=f"Output media file contains no valid video or audio streams: {dst_path.name}",
            dst_info=dst_info,
        )

    # Stream Presence Validation
    if src_info.has_video and not dst_info.has_video:
        return VerificationReport(
            is_valid=False,
            error_message=f"Output media is missing expected video stream: {dst_path.name}",
            dst_info=dst_info,
        )

    # Resolution Check (if video present)
    src_v = src_info.primary_video
    dst_v = dst_info.primary_video
    res_match = True
    if src_v and dst_v:
        res_match = (src_v.width == dst_v.width) and (src_v.height == dst_v.height)

    # Duration Parity Validation
    if src_info.duration > 3.0 and dst_info.duration > 0:
        diff = abs(src_info.duration - dst_info.duration)
        if diff > duration_tolerance_sec:
            error_msg = (
                f"Duration mismatch for {dst_path.name}: "
                f"expected ~{src_info.duration:.2f}s, got {dst_info.duration:.2f}s (delta: {diff:.2f}s)"
            )
            logger.error(error_msg)
            return VerificationReport(
                is_valid=False,
                error_message=error_msg,
                resolution_match=res_match,
                dst_info=dst_info,
            )

    return VerificationReport(
        is_valid=True,
        resolution_match=res_match,
        dst_info=dst_info,
        details={"file_size": file_size, "duration": dst_info.duration},
    )


def verify_output_file(
    dst_path: Path,
    src_info: MediaInfo,
    ffmpeg_path: Path,
    duration_tolerance_sec: float = 2.0,
) -> tuple[bool, str]:
    report = verify_output_file_detailed(dst_path, src_info, ffmpeg_path, duration_tolerance_sec)
    return report.is_valid, report.error_message

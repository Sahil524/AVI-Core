from pathlib import Path
from unittest.mock import patch

from avicore.models import MediaInfo, VideoStreamInfo
from avicore.verifier import verify_output_file_detailed


def test_verify_output_file_missing():
    src_info = MediaInfo(file_path=Path("src.mp4"), duration=10.0)
    # Output file does not exist
    report = verify_output_file_detailed(Path("nonexistent.mp4"), src_info, Path("ffmpeg.exe"))
    assert report.is_valid is False
    assert "does not exist" in report.error_message


@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.stat")
def test_verify_output_file_zero_bytes(mock_stat, mock_exists):
    mock_stat.return_value.st_size = 0
    src_info = MediaInfo(file_path=Path("src.mp4"), duration=10.0)
    report = verify_output_file_detailed(Path("zero.mp4"), src_info, Path("ffmpeg.exe"))
    assert report.is_valid is False
    assert "0 bytes" in report.error_message


@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.stat")
@patch("avicore.verifier.probe_media_file")
def test_verify_output_file_duration_mismatch(mock_probe, mock_stat, mock_exists):
    mock_stat.return_value.st_size = 1024

    src_info = MediaInfo(
        file_path=Path("src.mp4"),
        duration=100.0,
        video_streams=[VideoStreamInfo(index=0, codec="h264", width=1280, height=720)],
    )

    # Mock output file having duration 50.0 (delta = 50.0s > 2.0s tolerance)
    dst_info = MediaInfo(
        file_path=Path("dst.mp4"),
        duration=50.0,
        video_streams=[VideoStreamInfo(index=0, codec="h264", width=1280, height=720)],
    )
    mock_probe.return_value = dst_info

    report = verify_output_file_detailed(Path("dst.mp4"), src_info, Path("ffmpeg.exe"))
    assert report.is_valid is False
    assert "Duration mismatch" in report.error_message

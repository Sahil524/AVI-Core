import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from avicore.probe import (
    _probe_with_ffmpeg_fallback,
    _probe_with_ffprobe,
)

# Sample ffprobe JSON output
MOCK_FFPROBE_OUTPUT = {
    "format": {
        "format_name": "matroska,webm",
        "duration": "120.500000",
        "size": "5000000",
    },
    "streams": [
        {
            "index": 0,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "pix_fmt": "yuv420p",
            "color_primaries": "bt709",
            "color_transfer": "bt709",
            "color_space": "bt709",
            "duration": "120.500000",
        },
        {
            "index": 1,
            "codec_type": "audio",
            "codec_name": "aac",
            "sample_rate": "48000",
            "channels": 6,
            "channel_layout": "5.1",
            "bit_rate": "384000",
            "duration": "120.500000",
        },
    ],
    "chapters": [],
}


def test_probe_with_ffprobe():
    mock_run = MagicMock()
    mock_run.return_value.stdout = json.dumps(MOCK_FFPROBE_OUTPUT)
    mock_run.return_value.stderr = ""
    mock_run.return_value.returncode = 0

    with (
        patch("subprocess.run", mock_run),
        patch("pathlib.Path.exists", return_value=True),
    ):
        info = _probe_with_ffprobe(Path("dummy.mkv"), Path("ffprobe.exe"))

        assert info.format_name == "matroska,webm"
        assert info.duration == 120.5
        assert info.size_bytes == 5000000
        assert info.has_video is True
        assert info.has_audio is True
        assert info.primary_video is not None
        assert info.primary_video.codec == "h264"
        assert info.primary_video.width == 1920
        assert info.primary_video.height == 1080
        assert info.primary_audio is not None
        assert info.primary_audio.codec == "aac"
        assert info.primary_audio.channels == 6


def test_probe_with_ffmpeg_fallback():
    mock_stderr = """
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'dummy.mp4':
  Duration: 00:01:30.25, start: 0.000000, bitrate: 1205 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), 1280x720
  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 96 kb/s
"""
    mock_run = MagicMock()
    mock_run.return_value.stderr = mock_stderr
    mock_run.return_value.returncode = 1  # ffmpeg returns non-zero when run without output file, which is normal

    mock_stat = MagicMock()
    mock_stat.return_value.st_size = 5000000

    with (
        patch("subprocess.run", mock_run),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", mock_stat),
    ):
        info = _probe_with_ffmpeg_fallback(Path("dummy.mp4"), Path("ffmpeg.exe"))

        assert abs(info.duration - 90.25) < 0.01
        assert info.has_video is True
        assert info.has_audio is True
        assert info.primary_video is not None
        assert info.primary_video.codec == "h264"
        assert info.primary_video.width == 1280
        assert info.primary_video.height == 720
        assert info.primary_audio is not None
        assert info.primary_audio.codec == "aac"
        assert info.primary_audio.sample_rate == 44100
        assert info.size_bytes == 5000000

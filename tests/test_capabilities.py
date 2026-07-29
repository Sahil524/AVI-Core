from pathlib import Path
from unittest.mock import MagicMock, patch

from avicore.capabilities import detect_capabilities

MOCK_ENCODERS_OUTPUT = """
Encoders:
 V..... libx264              libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (codec h264)
 V..... h264_nvenc            NVIDIA NVENC H.264 encoder (codec h264)
 V..... h264_qsv              H.264 / AVC (Intel Quick Sync Video acceleration) (codec h264)
 A..... aac                  AAC (Advanced Audio Coding)
"""


def test_detect_capabilities():
    mock_run = MagicMock()
    mock_run.return_value.stdout = MOCK_ENCODERS_OUTPUT
    mock_run.return_value.stderr = ""
    mock_run.return_value.returncode = 0

    with (
        patch("subprocess.run", mock_run),
        patch("pathlib.Path.exists", return_value=True),
    ):
        # Force rebenchmark to bypass cache loading
        caps = detect_capabilities(Path("ffmpeg.exe"), force_rebenchmark=True)

        assert caps.has_nvenc is True
        assert caps.has_qsv is True
        assert caps.has_amf is False
        assert "h264_nvenc" in caps.available_encoders
        assert "h264_qsv" in caps.available_encoders
        assert "libx264" in caps.available_encoders
        assert "aac" in caps.available_encoders

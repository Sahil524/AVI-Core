from pathlib import Path

from avicore.models import AudioStreamInfo, MediaInfo, VideoStreamInfo
from avicore.optimizer import analyze_passthrough_opportunity


def test_analyze_passthrough_opportunity():
    # Video stream: h264, Audio stream: aac
    src_info = MediaInfo(
        file_path=Path("dummy.mkv"),
        duration=120.0,
        video_streams=[VideoStreamInfo(index=0, codec="h264", width=1920, height=1080)],
        audio_streams=[AudioStreamInfo(index=1, codec="aac")],
    )

    # Conversion to MP4 (both native to mp4 container)
    plan = analyze_passthrough_opportunity(src_info, "mp4")
    assert plan.can_copy_video is True
    assert plan.can_copy_audio is True
    assert plan.is_full_passthrough is True

    # Conversion to WebM (h264 is NOT native to webm, but VP9/AV1 is)
    plan_webm = analyze_passthrough_opportunity(src_info, "webm")
    assert plan_webm.can_copy_video is False
    assert plan_webm.can_copy_audio is False
    assert plan_webm.is_full_passthrough is False

    # Video stream: vp9, Audio stream: opus (native to WebM)
    src_webm = MediaInfo(
        file_path=Path("dummy.mkv"),
        duration=120.0,
        video_streams=[VideoStreamInfo(index=0, codec="vp9", width=1920, height=1080)],
        audio_streams=[AudioStreamInfo(index=1, codec="opus")],
    )
    plan_webm_ok = analyze_passthrough_opportunity(src_webm, "webm")
    assert plan_webm_ok.can_copy_video is True
    assert plan_webm_ok.can_copy_audio is True
    assert plan_webm_ok.is_full_passthrough is True

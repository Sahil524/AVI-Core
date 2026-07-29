from __future__ import annotations

from dataclasses import dataclass

from avicore.models import MediaInfo

CONTAINER_NATIVE_CODECS: dict[str, dict[str, set[str]]] = {
    "mp4": {
        "video": {"h264", "hevc", "av1", "vp9", "mpeg4"},
        "audio": {"aac", "mp3", "ac3", "eac3", "flac"},
    },
    "mkv": {
        "video": {"h264", "hevc", "av1", "vp9", "vp8", "mpeg4", "prores"},
        "audio": {"aac", "mp3", "flac", "opus", "vorbis", "ac3", "dts", "pcm_s16le"},
    },
    "mov": {
        "video": {"h264", "hevc", "prores", "mpeg4"},
        "audio": {"aac", "mp3", "pcm_s16le", "alac"},
    },
    "webm": {"video": {"vp9", "vp8", "av1"}, "audio": {"opus", "vorbis"}},
    "avi": {"video": {"mpeg4", "mjpeg", "h264"}, "audio": {"mp3", "pcm_s16le", "ac3"}},
}


@dataclass
class PassthroughPlan:
    can_copy_video: bool = False
    can_copy_audio: bool = False
    can_copy_subtitles: bool = False
    has_video: bool = False
    has_audio: bool = False

    @property
    def is_full_passthrough(self) -> bool:
        video_ok = (not self.has_video) or self.can_copy_video
        audio_ok = (not self.has_audio) or self.can_copy_audio
        return video_ok and audio_ok


def analyze_passthrough_opportunity(src_info: MediaInfo, target_format: str) -> PassthroughPlan:
    """Analyze if video/audio streams can be copied without transcoding (-c copy)."""
    fmt = target_format.lower().lstrip(".")
    if fmt not in CONTAINER_NATIVE_CODECS:
        return PassthroughPlan()

    native_v = CONTAINER_NATIVE_CODECS[fmt]["video"]
    native_a = CONTAINER_NATIVE_CODECS[fmt]["audio"]

    plan = PassthroughPlan(has_video=src_info.has_video, has_audio=src_info.has_audio)

    v_stream = src_info.primary_video
    if v_stream and v_stream.codec.lower() in native_v:
        plan.can_copy_video = True

    a_stream = src_info.primary_audio
    if a_stream and a_stream.codec.lower() in native_a:
        plan.can_copy_audio = True

    if fmt in {"mkv", "mp4"} and src_info.subtitle_streams:
        plan.can_copy_subtitles = True

    return plan

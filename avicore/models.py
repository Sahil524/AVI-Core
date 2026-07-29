from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoStreamInfo:
    index: int
    codec: str
    width: int
    height: int
    bit_depth: int = 8
    chroma_subsampling: str = "4:2:0"
    pix_fmt: str = ""
    color_space: str = ""
    color_primaries: str = ""
    color_trc: str = ""
    hdr_format: str = "sdr"  # sdr, hdr10, hlg, dolby_vision
    fps: float = 0.0
    is_vfr: bool = False
    rotation: int = 0
    is_hdr: bool = False
    has_alpha: bool = False
    duration: float = 0.0


@dataclass
class AudioStreamInfo:
    index: int
    codec: str
    sample_rate: int = 44100
    channels: int = 2
    channel_layout: str = ""
    bit_rate: int = 0
    duration: float = 0.0


@dataclass
class SubtitleStreamInfo:
    index: int
    codec: str
    language: str = ""
    is_image_based: bool = False


@dataclass
class MediaInfo:
    file_path: Path
    format_name: str = ""
    duration: float = 0.0
    size_bytes: int = 0
    has_icc: bool = False
    has_exif: bool = False
    chapters_count: int = 0
    attachments_count: int = 0
    video_streams: list[VideoStreamInfo] = field(default_factory=list)
    audio_streams: list[AudioStreamInfo] = field(default_factory=list)
    subtitle_streams: list[SubtitleStreamInfo] = field(default_factory=list)

    @property
    def has_video(self) -> bool:
        return len(self.video_streams) > 0

    @property
    def has_audio(self) -> bool:
        return len(self.audio_streams) > 0

    @property
    def primary_video(self) -> VideoStreamInfo | None:
        return self.video_streams[0] if self.video_streams else None

    @property
    def primary_audio(self) -> AudioStreamInfo | None:
        return self.audio_streams[0] if self.audio_streams else None

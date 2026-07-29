from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path

from avicore.models import (
    AudioStreamInfo,
    MediaInfo,
    SubtitleStreamInfo,
    VideoStreamInfo,
)

logger = logging.getLogger("avicore.probe")


def resolve_ffprobe_path(ffmpeg_path: Path) -> Path | None:
    ext = ".exe" if ffmpeg_path.suffix.lower() == ".exe" else ""
    candidate = ffmpeg_path.parent / f"ffprobe{ext}"
    if candidate.exists():
        return candidate
    return None


def probe_media_file(file_path: Path, ffmpeg_path: Path) -> MediaInfo:
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ffprobe = resolve_ffprobe_path(ffmpeg_path)
    if ffprobe:
        try:
            return _probe_with_ffprobe(file_path, ffprobe)
        except Exception as exc:
            logger.warning(f"ffprobe failed for {file_path}, attempting ffmpeg fallback: {exc}")

    return _probe_with_ffmpeg_fallback(file_path, ffmpeg_path)


def _probe_with_ffprobe(file_path: Path, ffprobe_path: Path) -> MediaInfo:
    cmd = [
        str(ffprobe_path),
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        "-show_chapters",
        str(file_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)

    format_info = data.get("format", {})
    streams_info = data.get("streams", [])
    chapters = data.get("chapters", [])

    media_info = MediaInfo(
        file_path=file_path,
        format_name=format_info.get("format_name", ""),
        duration=float(format_info.get("duration", 0.0) or 0.0),
        size_bytes=int(format_info.get("size", 0) or file_path.stat().st_size),
        chapters_count=len(chapters),
    )

    for st in streams_info:
        codec_type = st.get("codec_type")
        idx = int(st.get("index", 0))
        codec_name = st.get("codec_name", "")

        if codec_type == "video":
            pix_fmt = st.get("pix_fmt", "")
            color_primaries = st.get("color_primaries", "")
            color_trc = st.get("color_transfer", "") or st.get("color_trc", "")
            colorspace = st.get("color_space", "")

            # Bit Depth
            bits_raw = st.get("bits_per_raw_sample")
            if bits_raw and str(bits_raw).isdigit():
                bit_depth = int(bits_raw)
            elif "10" in pix_fmt:
                bit_depth = 10
            elif "12" in pix_fmt:
                bit_depth = 12
            else:
                bit_depth = 8

            # HDR Detection
            hdr_format = "sdr"
            if "dovi" in str(st).lower() or "dolby vision" in str(st).lower():
                hdr_format = "dolby_vision"
            elif color_trc == "arib-std-b67":
                hdr_format = "hlg"
            elif color_primaries == "bt2020" or color_trc == "smpte2084":
                hdr_format = "hdr10"

            is_hdr = hdr_format != "sdr" or bit_depth > 8
            has_alpha = "alpha" in pix_fmt or pix_fmt in {
                "rgba",
                "bgra",
                "yuva420p",
                "yuva422p",
                "yuva444p",
            }

            # Rotation parsing
            rotation = 0
            tags = st.get("tags", {})
            if "rotate" in tags:
                try:
                    rotation = int(tags["rotate"])
                except ValueError:
                    pass

            v_info = VideoStreamInfo(
                index=idx,
                codec=codec_name,
                width=int(st.get("width", 0) or 0),
                height=int(st.get("height", 0) or 0),
                bit_depth=bit_depth,
                chroma_subsampling="4:4:4" if "444" in pix_fmt else "4:2:0",
                pix_fmt=pix_fmt,
                color_space=colorspace,
                color_primaries=color_primaries,
                color_trc=color_trc,
                hdr_format=hdr_format,
                is_hdr=is_hdr,
                has_alpha=has_alpha,
                rotation=rotation,
                duration=float(st.get("duration", 0.0) or media_info.duration),
            )
            media_info.video_streams.append(v_info)

        elif codec_type == "audio":
            a_info = AudioStreamInfo(
                index=idx,
                codec=codec_name,
                sample_rate=int(st.get("sample_rate", 44100) or 44100),
                channels=int(st.get("channels", 2) or 2),
                channel_layout=st.get("channel_layout", ""),
                bit_rate=int(st.get("bit_rate", 0) or 0),
                duration=float(st.get("duration", 0.0) or media_info.duration),
            )
            media_info.audio_streams.append(a_info)

        elif codec_type == "subtitle":
            is_img = codec_name in {
                "hdmv_pgs_subtitle",
                "dvd_subtitle",
                "dvdsub",
                "pgssub",
            }
            s_info = SubtitleStreamInfo(
                index=idx,
                codec=codec_name,
                language=st.get("tags", {}).get("language", ""),
                is_image_based=is_img,
            )
            media_info.subtitle_streams.append(s_info)

        elif codec_type == "attachment":
            media_info.attachments_count += 1

    return media_info


def _probe_with_ffmpeg_fallback(file_path: Path, ffmpeg_path: Path) -> MediaInfo:
    cmd = [str(ffmpeg_path), "-hide_banner", "-i", str(file_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    output = res.stderr

    media_info = MediaInfo(
        file_path=file_path,
        size_bytes=file_path.stat().st_size if file_path.exists() else 0,
    )

    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if dur_match:
        hrs, mins, secs = dur_match.groups()
        media_info.duration = float(hrs) * 3600 + float(mins) * 60 + float(secs)

    vid_match = re.search(
        r"Stream #\d+:(\d+).*?Video:\s*([a-zA-Z0-9_-]+).*?,.*?(\d{2,5})x(\d{2,5})",
        output,
    )
    if vid_match:
        idx, codec, w, h = vid_match.groups()
        media_info.video_streams.append(
            VideoStreamInfo(
                index=int(idx),
                codec=codec,
                width=int(w),
                height=int(h),
                duration=media_info.duration,
            )
        )

    aud_match = re.search(r"Stream #\d+:(\d+).*?Audio:\s*([a-zA-Z0-9_-]+).*?,\s*(\d+)\s*Hz", output)
    if aud_match:
        idx, codec, hz = aud_match.groups()
        media_info.audio_streams.append(
            AudioStreamInfo(
                index=int(idx),
                codec=codec,
                sample_rate=int(hz),
                duration=media_info.duration,
            )
        )

    return media_info

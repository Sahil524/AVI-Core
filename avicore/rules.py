from __future__ import annotations

from pathlib import Path

from avicore.capabilities import HWCapabilities
from avicore.models import MediaInfo

CONTAINER_MAP: dict[str, dict[str, str | None]] = {
    "mkv": {"v": "libx264", "a": "aac", "s": "copy"},
    "mp4": {"v": "libx264", "a": "aac", "s": "mov_text"},
    "m4v": {"v": "libx264", "a": "aac", "s": "mov_text"},
    "mov": {"v": "libx264", "a": "aac", "s": "mov_text"},
    "webm": {"v": "libvpx-vp9", "a": "libopus", "s": None},
    "avi": {"v": "libxvid", "a": "libmp3lame", "s": None},
    "flv": {"v": "libx264", "a": "aac", "s": None},
    "ts": {"v": "libx264", "a": "aac", "s": None},
}


def resolve_best_video_encoder(
    target_format: str, default_codec: str, caps: HWCapabilities | None = None
) -> str:
    """Select optimal video encoder with graceful GPU fallback chain (NVENC -> QSV -> AMF -> CPU)."""
    if not caps or target_format == "webm" or default_codec != "libx264":
        return default_codec

    if caps.has_nvenc and "h264_nvenc" in caps.available_encoders:
        return "h264_nvenc"
    elif caps.has_qsv and "h264_qsv" in caps.available_encoders:
        return "h264_qsv"
    elif caps.has_amf and "h264_amf" in caps.available_encoders:
        return "h264_amf"

    return default_codec


def build_video_convert_command(
    ffmpeg_path: Path,
    src_info: MediaInfo,
    dst_path: Path,
    target_format: str,
    fast: bool = False,
    caps: HWCapabilities | None = None,
) -> list[str]:
    target_format = target_format.lower().lstrip(".")

    if fast:
        return [
            str(ffmpeg_path),
            "-y",
            "-i",
            str(src_info.file_path),
            "-map",
            "0",
            "-c",
            "copy",
            str(dst_path),
        ]

    cmd = [str(ffmpeg_path), "-y", "-i", str(src_info.file_path)]
    cmd += ["-map", "0:v:0?", "-map", "0:a:0?", "-map", "0:s:0?", "-map_metadata", "0"]

    cfg = CONTAINER_MAP.get(target_format, {"v": "libx264", "a": "aac"})
    vcodec = resolve_best_video_encoder(target_format, cfg["v"] or "libx264", caps)
    acodec = cfg["a"] or "aac"

    cmd += ["-c:v", vcodec]

    # Video Filters & Color Space
    v_stream = src_info.primary_video
    if v_stream and v_stream.is_hdr and target_format == "webm":
        cmd += [
            "-vf",
            "zimg=transfer=bt709:prime=bt709:colormatrix=bt709",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
        ]
    else:
        cmd += [
            "-pix_fmt",
            "yuv420p",
            "-fps_mode",
            "passthrough",
            "-color_primaries",
            "bt709",
            "-color_trc",
            "bt709",
            "-colorspace",
            "bt709",
        ]

    if vcodec == "libx264":
        cmd += ["-profile:v", "high", "-level", "4.1"]

    if src_info.has_audio:
        cmd += ["-c:a", acodec]
        a_stream = src_info.primary_audio
        if a_stream and a_stream.channels > 2:
            cmd += [
                "-af",
                "pan=stereo|FL=0.5*FC+0.707*FL+0.707*BL|FR=0.5*FC+0.707*FR+0.707*BR",
            ]
        else:
            cmd += ["-ac", "2", "-ar", "48000"]
    else:
        cmd += ["-an"]

    if target_format in {"mp4", "mov", "m4v"}:
        cmd += ["-movflags", "+faststart"]
        sub_stream = src_info.subtitle_streams[0] if src_info.subtitle_streams else None
        if sub_stream and not sub_stream.is_image_based:
            cmd += ["-c:s", "mov_text"]
        else:
            cmd += ["-sn"]
    elif target_format == "mkv":
        cmd += ["-c:s", "copy"]
    else:
        cmd += ["-sn"]

    cmd += ["-dn", "-max_muxing_queue_size", "4096", str(dst_path)]
    return cmd


def build_image_convert_command(
    ffmpeg_path: Path, src_info: MediaInfo, dst_path: Path, target_format: str
) -> list[str]:
    target_format = target_format.lower().lstrip(".")
    cmd = [str(ffmpeg_path), "-y", "-i", str(src_info.file_path), "-map_metadata", "0"]

    v_stream = src_info.primary_video
    if v_stream and v_stream.has_alpha and target_format in {"jpg", "jpeg"}:
        cmd += [
            "-vf",
            "split[s0][s1];[s0]fill=color=white[bg];[bg][s1]overlay=format=auto",
        ]

    if target_format in {"jpg", "jpeg"}:
        cmd += ["-q:v", "2"]
    elif target_format == "webp":
        cmd += ["-quality", "90"]

    cmd.append(str(dst_path))
    return cmd


def build_image_compress_command(
    ffmpeg_path: Path, src_info: MediaInfo, dst_path: Path, quality: int = 60
) -> list[str]:
    ext = src_info.file_path.suffix.lower()
    cmd = [str(ffmpeg_path), "-y", "-i", str(src_info.file_path), "-map_metadata", "0"]

    if ext == ".png":
        cmd += ["-compression_level", "9"]
    else:
        q = max(2, min(31, int((100 - quality) / 3)))
        cmd += ["-q:v", str(q)]

    cmd.append(str(dst_path))
    return cmd

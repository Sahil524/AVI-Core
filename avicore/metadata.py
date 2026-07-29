from __future__ import annotations

from dataclasses import dataclass

from avicore.models import MediaInfo


@dataclass
class MetadataRules:
    preserve_exif: bool = True
    preserve_icc: bool = True
    preserve_chapters: bool = True
    preserve_attachments: bool = False
    map_metadata_flag: str = "-map_metadata 0"


CONTAINER_METADATA_CAPABILITIES = {
    "mp4": {"exif": False, "icc": False, "chapters": True, "cover_art": True},
    "mkv": {"exif": True, "icc": True, "chapters": True, "cover_art": True},
    "mov": {"exif": False, "icc": False, "chapters": True, "cover_art": True},
    "webm": {"exif": False, "icc": False, "chapters": False, "cover_art": False},
    "jpg": {"exif": True, "icc": True, "chapters": False, "cover_art": False},
    "jpeg": {"exif": True, "icc": True, "chapters": False, "cover_art": False},
    "png": {"exif": True, "icc": True, "chapters": False, "cover_art": False},
    "webp": {"exif": True, "icc": True, "chapters": False, "cover_art": False},
    "avif": {"exif": True, "icc": True, "chapters": False, "cover_art": False},
    "mp3": {"exif": False, "icc": False, "chapters": True, "cover_art": True},
    "flac": {"exif": False, "icc": False, "chapters": True, "cover_art": True},
}


def resolve_metadata_rules(src_info: MediaInfo, target_format: str) -> MetadataRules:
    """Resolve container-safe metadata preservation rules."""
    fmt = target_format.lower().lstrip(".")
    caps = CONTAINER_METADATA_CAPABILITIES.get(fmt, {"exif": True, "icc": True, "chapters": True, "cover_art": True})

    return MetadataRules(
        preserve_exif=caps["exif"] and src_info.has_exif,
        preserve_icc=caps["icc"] and src_info.has_icc,
        preserve_chapters=caps["chapters"] and src_info.chapters_count > 0,
        preserve_attachments=caps["cover_art"] and src_info.attachments_count > 0,
        map_metadata_flag="-map_metadata 0",
    )


def build_metadata_ffmpeg_flags(rules: MetadataRules) -> list[str]:
    """Generate FFmpeg flags corresponding to metadata rules."""
    flags = [rules.map_metadata_flag]
    if rules.preserve_chapters:
        flags.append("-map_chapters 0")
    return flags

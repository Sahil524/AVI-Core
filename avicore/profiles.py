from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConversionProfile:
    name: str
    description: str
    crf: int | None = 22
    preset: str = "medium"
    audio_bitrate: str = "192k"
    max_bitrate: str | None = None
    preserve_metadata: bool = True
    movflags: list[str] = field(default_factory=lambda: ["+faststart"])


PROFILES: dict[str, ConversionProfile] = {
    "maximum_quality": ConversionProfile(
        name="maximum_quality",
        description="Highest visual fidelity for archival and high-end displays.",
        crf=18,
        preset="slow",
        audio_bitrate="320k",
    ),
    "balanced": ConversionProfile(
        name="balanced",
        description="Standard trade-off between speed, file size, and visual quality.",
        crf=22,
        preset="medium",
        audio_bitrate="192k",
    ),
    "fast": ConversionProfile(
        name="fast",
        description="Rapid encoding for quick previews or low-CPU environments.",
        crf=26,
        preset="fast",
        audio_bitrate="128k",
    ),
    "lossless": ConversionProfile(
        name="lossless",
        description="Math loss-free encoding (large output sizes).",
        crf=0,
        preset="veryslow",
        audio_bitrate="320k",
    ),
    "archive": ConversionProfile(
        name="archive",
        description="Long-term storage optimized for space and quality.",
        crf=20,
        preset="slower",
        audio_bitrate="256k",
    ),
    "web_optimized": ConversionProfile(
        name="web_optimized",
        description="Fast start streaming for web browsers and HTML5 video.",
        crf=23,
        preset="medium",
        audio_bitrate="160k",
        movflags=["+faststart"],
    ),
    "youtube": ConversionProfile(
        name="youtube",
        description="Optimized specs for YouTube upload processing.",
        crf=18,
        preset="slow",
        audio_bitrate="320k",
        movflags=["+faststart"],
    ),
    "instagram": ConversionProfile(
        name="instagram",
        description="Targeted specs for Instagram feed and Reels.",
        crf=22,
        preset="medium",
        audio_bitrate="192k",
        max_bitrate="5M",
        movflags=["+faststart"],
    ),
    "tiktok": ConversionProfile(
        name="tiktok",
        description="Targeted specs for TikTok video uploads.",
        crf=22,
        preset="medium",
        audio_bitrate="192k",
        max_bitrate="5M",
        movflags=["+faststart"],
    ),
    "discord": ConversionProfile(
        name="discord",
        description="Low file size for Discord free tier file attachment limits.",
        crf=28,
        preset="fast",
        audio_bitrate="128k",
        max_bitrate="2M",
        movflags=["+faststart"],
    ),
    "whatsapp": ConversionProfile(
        name="whatsapp",
        description="Aggressive compression for instant messaging uploads.",
        crf=28,
        preset="fast",
        audio_bitrate="96k",
        max_bitrate="1.5M",
        movflags=["+faststart"],
    ),
}


def resolve_profile(profile_name: str) -> ConversionProfile:
    """Resolve a profile by name, defaulting to 'balanced' if unrecognized."""
    key = profile_name.lower().strip()
    return PROFILES.get(key, PROFILES["balanced"])

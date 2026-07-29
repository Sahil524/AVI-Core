from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from avicore.capabilities import HWCapabilities, detect_capabilities
from avicore.metadata import MetadataRules, resolve_metadata_rules
from avicore.models import MediaInfo
from avicore.optimizer import PassthroughPlan, analyze_passthrough_opportunity
from avicore.probe import probe_media_file
from avicore.profiles import ConversionProfile, resolve_profile
from avicore.rules import (
    build_image_convert_command,
    build_video_convert_command,
)


@dataclass
class PipelineContext:
    src_path: Path
    dst_path: Path
    target_format: str
    ffmpeg_path: Path
    profile_name: str = "balanced"
    fast: bool = False
    quality: int = 60

    # Internal Stage Outputs
    src_info: MediaInfo | None = None
    capabilities: HWCapabilities | None = None
    profile: ConversionProfile | None = None
    passthrough_plan: PassthroughPlan | None = None
    metadata_rules: MetadataRules | None = None
    ffmpeg_command: list[str] | None = None


class MediaProcessingPipeline:
    """Orchestrates structured multi-stage media conversion pipelines."""

    def __init__(self, ffmpeg_path: Path):
        self.ffmpeg_path = ffmpeg_path

    def prepare_video_pipeline(
        self,
        src_path: Path,
        dst_path: Path,
        target_format: str,
        profile_name: str = "balanced",
        fast: bool = False,
    ) -> PipelineContext:
        ctx = PipelineContext(
            src_path=src_path,
            dst_path=dst_path,
            target_format=target_format,
            ffmpeg_path=self.ffmpeg_path,
            profile_name=profile_name,
            fast=fast,
        )

        # Stage 1: Analyze
        ctx.src_info = probe_media_file(src_path, self.ffmpeg_path)

        # Stage 2: Capability Detection
        ctx.capabilities = detect_capabilities(self.ffmpeg_path)

        # Stage 3: Profile Resolution
        ctx.profile = resolve_profile(profile_name)

        # Stage 4: Passthrough Check
        ctx.passthrough_plan = analyze_passthrough_opportunity(ctx.src_info, target_format)

        # Stage 5: Metadata Resolution
        ctx.metadata_rules = resolve_metadata_rules(ctx.src_info, target_format)

        # Stage 6: Command Generation
        ctx.ffmpeg_command = build_video_convert_command(
            ffmpeg_path=self.ffmpeg_path,
            src_info=ctx.src_info,
            dst_path=dst_path,
            target_format=target_format,
            fast=fast or (ctx.passthrough_plan.is_full_passthrough and profile_name == "fast"),
            caps=ctx.capabilities,
        )

        return ctx

    def prepare_image_pipeline(
        self, src_path: Path, dst_path: Path, target_format: str, quality: int = 60
    ) -> PipelineContext:
        ctx = PipelineContext(
            src_path=src_path,
            dst_path=dst_path,
            target_format=target_format,
            ffmpeg_path=self.ffmpeg_path,
            quality=quality,
        )

        ctx.src_info = probe_media_file(src_path, self.ffmpeg_path)
        ctx.capabilities = detect_capabilities(self.ffmpeg_path)
        ctx.metadata_rules = resolve_metadata_rules(ctx.src_info, target_format)
        ctx.ffmpeg_command = build_image_convert_command(self.ffmpeg_path, ctx.src_info, dst_path, target_format)

        return ctx

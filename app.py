from __future__ import annotations

import glob
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import click

from avicore.atomic import commit_two_phase_output
from avicore.batch import BatchProcessor
from avicore.diagnostics import generate_support_bundle
from avicore.logger import setup_production_logging
from avicore.pipeline import MediaProcessingPipeline
from avicore.probe import probe_media_file
from avicore.rules import build_image_compress_command

IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp"}
VIDEO_FORMATS = {"mp4", "mkv", "mov", "avi", "webm", "m4v", "flv", "ts"}
AUDIO_FORMATS = {"mp3", "wav", "aac", "flac", "ogg", "m4a"}

# ============================================================
# Version
# ============================================================

APP_VERSION: str = "2.0.0"

# ============================================================
# Globals / State
# ============================================================

CREATED_FILES: list[Path] = []
LOG_FILE: Path = Path("avicore.log")

# ============================================================
# Logging
# ============================================================


def setup_logging(verbose: bool) -> None:
    setup_production_logging(LOG_FILE, verbose=verbose)


# ============================================================
# FFmpeg Resolution & Verification
# ============================================================


def resolve_ffmpeg() -> Path:
    ext = ".exe" if os.name == "nt" else ""
    if hasattr(sys, "_MEIPASS"):
        candidate = Path(sys._MEIPASS) / f"ffmpeg{ext}"
    else:
        candidate = Path(__file__).parent / "bin" / f"ffmpeg{ext}"
    return candidate


def verify_ffmpeg(ffmpeg: Path) -> None:
    if not ffmpeg.exists():
        raise click.ClickException(f"FFmpeg not found.\nExpected location: {ffmpeg.resolve()}")

    try:
        result = subprocess.run(
            [str(ffmpeg), "-version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    except Exception as exc:
        raise click.ClickException(
            f"FFmpeg self-diagnostic failed.\nBinary path: {ffmpeg.resolve()}\nReason: {exc}"
        ) from exc


# ============================================================
# Safety & Cleanup
# ============================================================


def register_cleanup() -> None:
    def _handler(sig, frame=None):
        click.secho("\nInterrupted. Cleaning up partial outputs......", fg="yellow")
        for f in CREATED_FILES:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                logging.exception("Cleanup failed")
        sys.exit(130)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def suggest_path(path: Path) -> Path:
    base = path.stem
    suffix = path.suffix
    parent = path.parent
    idx = 1
    while True:
        candidate = parent / f"{base}_{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


# ============================================================
# Subprocess Wrapper
# ============================================================


def run_ffmpeg(cmd: list[str], dry_run: bool = False) -> bool:
    logging.debug("FFmpeg cmd: %s", " ".join(cmd))

    if dry_run:
        click.secho("[DRY-RUN] " + " ".join(cmd), fg="cyan")
        return True

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logging.error(result.stderr)
            click.secho("FFmpeg failed. See avicore.log for details.", fg="red")
            return False

        return True

    except Exception as exc:
        logging.exception("Execution failure")
        click.secho(f"Execution error: {exc}", fg="red")
        return False


# ============================================================
# Input Expansion (Windows-safe)
# ============================================================


def expand_inputs(inputs) -> list[Path]:
    results = []

    for item in inputs:
        matches = glob.glob(item)
        if matches:
            results.extend(matches)
        else:
            p = Path(item)
            if p.exists():
                results.append(str(p))

    return list(dict.fromkeys(Path(p) for p in results))


# ============================================================
# CLI Root
# ============================================================


@click.group(context_settings={"help_option_names": []})
@click.option("--verbose", is_flag=True, help="Enable detailed logging to avicore.log")
@click.option("--dry-run", is_flag=True, help="Preview commands without executing")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, dry_run: bool) -> None:
    setup_logging(verbose)
    register_cleanup()

    ffmpeg = resolve_ffmpeg()
    verify_ffmpeg(ffmpeg)

    ctx.obj = {
        "ffmpeg": ffmpeg,
        "verbose": verbose,
        "dry_run": dry_run,
    }


# ============================================================
# VERSION & HELP
# ============================================================


@cli.command(help="Display avicore version.")
def version() -> None:
    click.secho(f"avicore v{APP_VERSION}", fg="green")


@cli.command()
def help():
    click.echo("""
AVI CORE -- Simple Media Toolkit (v2.0 Architecture)

USAGE:

  avicore image convert <files> <format>
  avicore image compress <files>

  avicore video convert <files> <format>
  avicore video mute <files>

  avicore audio convert <files> <format>
  avicore audio extract <video>

  avicore system diagnostics

GLOBAL OPTIONS:

 --dry-run     Preview operations
 --verbose     Debug logging

""")


# ============================================================
# SYSTEM DIAGNOSTICS
# ============================================================


@cli.group()
def system():
    pass


@system.command(help="Generate diagnostic bundle ZIP file for bug reporting.")
@click.pass_context
def diagnostics(ctx: click.Context) -> None:
    ffmpeg: Path = ctx.obj["ffmpeg"]
    zip_path = generate_support_bundle(ffmpeg, Path("."))
    click.secho(f"Diagnostic bundle generated successfully: {zip_path.name}", fg="green")


# ============================================================
# VIDEO
# ============================================================


@cli.group()
def video():
    pass


def make_progress_callback(label: str):
    def callback(report):
        percent = report.percent_complete
        eta_str = f"{report.eta_seconds}s" if report.eta_seconds > 0 else "N/A"
        click.echo(
            f"\r[{percent}%] {label}: {report.completed_items}/{report.total_items} complete (Failed: {report.failed_items}, ETA: {eta_str})",  # noqa: E501
            nl=False,
        )
        if percent >= 100.0:
            click.echo()

    return callback


@video.command("convert", help="Universal video convert (container-aware + codec-safe).")
@click.argument("input", nargs=-1)
@click.argument("format")
@click.option("--fast", is_flag=True, help="Attempt stream copy first.")
@click.option("--force", is_flag=True, help="Overwrite if output exists.")
@click.pass_context
def video_convert(ctx: click.Context, input: tuple[str, ...], format: str, fast: bool, force: bool) -> None:

    format = format.lower().strip().lstrip(".")
    if not format.isalnum() or format not in VIDEO_FORMATS:
        raise click.ClickException(f"Unsupported video format: {format}")

    files = expand_inputs(input)
    if not files:
        raise click.ClickException("No input files resolved")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]
    pipeline = MediaProcessingPipeline(ffmpeg)

    def convert_video_worker(src: Path) -> tuple[bool, str]:
        if not src.exists() or not src.is_file():
            return False, f"Invalid source file: {src.name}"

        src_ext = src.suffix.lower().lstrip(".")
        if src_ext == format:
            return False, f"Source and target formats are identical (.{src_ext})"

        dst = src.with_name(src.stem + "." + format)

        if dst.exists():
            if not force:
                return False, f"Skipping existing file: {dst.name}"
            dst.unlink(missing_ok=True)

        temp_output = dst.with_name(dst.stem + "_tmp" + dst.suffix)

        pipe_ctx = pipeline.prepare_video_pipeline(
            src_path=src,
            dst_path=temp_output,
            target_format=format,
            profile_name="balanced",
            fast=fast,
        )

        if pipe_ctx.ffmpeg_command is None:
            return False, "FFmpeg command generation failed"
        if pipe_ctx.src_info is None:
            return False, "Source media info not resolved"

        encode_cmd = pipe_ctx.ffmpeg_command
        src_info = pipe_ctx.src_info

        if run_ffmpeg(encode_cmd, dry_run):
            success, err_msg = commit_two_phase_output(
                temp_output=temp_output,
                final_dst=dst,
                src=src,
                src_info=src_info,
                ffmpeg_path=ffmpeg,
                do_backup=True,
                dry_run=dry_run,
            )
            if success:
                CREATED_FILES.append(dst)
                return True, ""
            else:
                return False, f"Commit failed: {err_msg}"
        else:
            try:
                if temp_output.exists():
                    temp_output.unlink()
            except OSError:
                pass
            return False, "FFmpeg encoding failed"

    processor = BatchProcessor(progress_callback=make_progress_callback("Converting videos"))
    ok, fail, errors = processor.run_batch(files, convert_video_worker, is_video=True)

    if errors:
        click.secho("\nErrors encountered during processing:", fg="red")
        for err in errors:
            click.echo(err)

    click.secho(
        f"Completed -> Success: {ok} | Failed: {fail}",
        fg="green" if not fail else "yellow",
    )


@video.command("mute", help="Universal mute (removes all audio streams safely).")
@click.argument("input", nargs=-1)
@click.option("--force", is_flag=True, help="Overwrite if output exists.")
@click.pass_context
def video_mute(ctx: click.Context, input: tuple[str, ...], force: bool) -> None:

    files = expand_inputs(input)
    if not files:
        raise click.ClickException("No input files resolved")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    def mute_video_worker(src: Path) -> tuple[bool, str]:
        if not src.exists() or not src.is_file():
            return False, f"Invalid source file: {src.name}"

        if force:
            dst = src
        else:
            dst = src.with_name(src.stem + "_muted" + src.suffix)
            if dst.exists():
                dst = suggest_path(dst)

        temp_output = dst.with_name(dst.stem + "_muted_tmp" + dst.suffix)
        temp_output.unlink(missing_ok=True)

        cmd = [
            str(ffmpeg),
            "-y",
            "-i",
            str(src),
            "-map",
            "0:v?",
            "-map",
            "0:s?",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            "-an",
            "-max_muxing_queue_size",
            "4096",
            str(temp_output),
        ]

        if run_ffmpeg(cmd, dry_run):
            src_info = probe_media_file(src, ffmpeg)
            success, err_msg = commit_two_phase_output(
                temp_output=temp_output,
                final_dst=dst,
                src=src,
                src_info=src_info,
                ffmpeg_path=ffmpeg,
                do_backup=True,
                dry_run=dry_run,
            )
            if success:
                CREATED_FILES.append(dst)
                return True, ""
            else:
                return False, f"Commit failed: {err_msg}"
        else:
            try:
                if temp_output.exists():
                    temp_output.unlink()
            except OSError:
                pass
            return False, "FFmpeg failed"

    processor = BatchProcessor(progress_callback=make_progress_callback("Muting videos"))
    ok, fail, errors = processor.run_batch(files, mute_video_worker, is_video=True)

    if errors:
        click.secho("\nErrors encountered during processing:", fg="red")
        for err in errors:
            click.echo(err)

    click.secho(
        f"Completed -> Success: {ok} | Failed: {fail}",
        fg="green" if not fail else "yellow",
    )


# ============================================================
# IMAGE
# ============================================================


@cli.group()
def image():
    pass


@image.command("convert", help="Convert image(s).\nExample:\n avicore image convert *.png webp")
@click.argument("pattern", nargs=-1)
@click.argument("format")
@click.option("--force", is_flag=True)
@click.pass_context
def image_convert(ctx: click.Context, pattern: tuple[str, ...], format: str, force: bool) -> None:
    if not pattern:
        raise click.ClickException("At least one input pattern must be provided.")

    target_format = format.strip().lower().lstrip(".")
    if not target_format.isalnum():
        raise click.ClickException("Invalid format specified.")

    files = expand_inputs(pattern)
    if not files:
        raise click.ClickException("No input files resolved.")

    ffmpeg = ctx.obj.get("ffmpeg")
    dry_run = ctx.obj.get("dry_run", False)
    pipeline = MediaProcessingPipeline(ffmpeg)

    def convert_image_worker(src: Path) -> tuple[bool, str]:
        src_ext = src.suffix.lower().lstrip(".")
        if src_ext == target_format:
            return False, f"Source and target formats are identical (.{src_ext})"

        dst = src.with_suffix(f".{target_format}")
        if dst.exists() and not force:
            dst = suggest_path(dst)

        temp_output = dst.with_name(dst.stem + "_img_tmp" + dst.suffix)

        pipe_ctx = pipeline.prepare_image_pipeline(src, temp_output, target_format)
        if pipe_ctx.ffmpeg_command is None:
            return False, "FFmpeg command generation failed"
        if pipe_ctx.src_info is None:
            return False, "Source media info not resolved"

        cmd = pipe_ctx.ffmpeg_command
        src_info = pipe_ctx.src_info

        if run_ffmpeg(cmd, dry_run):
            success, err_msg = commit_two_phase_output(
                temp_output=temp_output,
                final_dst=dst,
                src=src,
                src_info=src_info,
                ffmpeg_path=ffmpeg,
                do_backup=True,
                dry_run=dry_run,
            )
            if success:
                CREATED_FILES.append(dst)
                return True, ""
            else:
                return False, f"Commit failed: {err_msg}"
        else:
            return False, "FFmpeg image conversion failed"

    processor = BatchProcessor(progress_callback=make_progress_callback("Converting images"))
    ok, fail, errors = processor.run_batch(files, convert_image_worker, is_video=False)

    if errors:
        click.secho("\nErrors encountered during processing:", fg="red")
        for err in errors:
            click.echo(err)

    click.secho(
        f"Completed -> Success: {ok} | Failed: {fail}",
        fg="green" if not fail else "yellow",
    )


@image.command(
    "compress",
    help="Compress images intelligently.\nExample:\n avicore image compress *.jpg --quality 70",
)
@click.argument("pattern", nargs=-1)
@click.option("--quality", default=60, show_default=True)
@click.option("--force", is_flag=True)
@click.pass_context
def image_compress(ctx: click.Context, pattern: tuple[str, ...], quality: int, force: bool) -> None:
    files = expand_inputs(pattern)
    if not files:
        raise click.ClickException("No input files resolved.")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    def compress_image_worker(src: Path) -> tuple[bool, str]:
        dst = src
        if dst.exists() and not force:
            dst = suggest_path(dst)

        temp_output = dst.with_name(dst.stem + "_comp_tmp" + dst.suffix)

        src_info = probe_media_file(src, ffmpeg)
        cmd = build_image_compress_command(ffmpeg, src_info, temp_output, quality)

        if run_ffmpeg(cmd, dry_run):
            success, err_msg = commit_two_phase_output(
                temp_output=temp_output,
                final_dst=dst,
                src=src,
                src_info=src_info,
                ffmpeg_path=ffmpeg,
                do_backup=True,
                dry_run=dry_run,
            )
            if success:
                CREATED_FILES.append(dst)
                return True, ""
            else:
                return False, f"Commit failed: {err_msg}"
        else:
            return False, "FFmpeg image compression failed"

    processor = BatchProcessor(progress_callback=make_progress_callback("Compressing images"))
    ok, fail, errors = processor.run_batch(files, compress_image_worker, is_video=False)

    if errors:
        click.secho("\nErrors encountered during processing:", fg="red")
        for err in errors:
            click.echo(err)

    click.secho(
        f"Completed -> Success: {ok} | Failed: {fail}",
        fg="green" if not fail else "yellow",
    )


# ============================================================
# AUDIO COMMANDS
# ============================================================


@cli.group()
def audio():
    pass


@audio.command(
    "extract",
    help="Extract audio from video.\n\nExample:\n  avicore audio extract input.mp4",
)
@click.argument("input")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def audio_extract(ctx: click.Context, input: str, force: bool) -> None:
    src = Path(input)
    if not src.exists():
        raise click.ClickException(f"Input not found: {src}")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    src_info = probe_media_file(src, ffmpeg)
    if not src_info.has_audio or not src_info.primary_audio:
        raise click.ClickException("Input file has no audio stream to extract.")

    codec = src_info.primary_audio.codec.lower()

    AUDIO_EXTENSION_MAP = {
        "aac": ".m4a",
        "mp3": ".mp3",
        "opus": ".opus",
        "vorbis": ".ogg",
        "flac": ".flac",
        "ac3": ".ac3",
        "dts": ".dts",
        "alac": ".m4a",
    }
    ext = AUDIO_EXTENSION_MAP.get(codec, ".mp3")

    dst = src.with_suffix(ext)
    if dst.exists() and not force:
        dst = suggest_path(dst)

    temp_output = dst.with_name(dst.stem + "_ext_tmp" + dst.suffix)

    if ext != ".mp3" or codec == "mp3":
        cmd = [
            str(ffmpeg),
            "-y",
            "-i",
            str(src),
            "-vn",
            "-c:a",
            "copy",
            str(temp_output),
        ]
    else:
        cmd = [
            str(ffmpeg),
            "-y",
            "-i",
            str(src),
            "-vn",
            "-ab",
            "192k",
            "-map",
            "a",
            str(temp_output),
        ]

    if run_ffmpeg(cmd, dry_run):
        success, _err_msg = commit_two_phase_output(
            temp_output=temp_output,
            final_dst=dst,
            src=src,
            src_info=src_info,
            ffmpeg_path=ffmpeg,
            do_backup=True,
            dry_run=dry_run,
        )
        if success:
            CREATED_FILES.append(dst)
            click.secho(f"Extracted -> {dst}", fg="green")


@audio.command(
    "convert",
    help="Convert audio format.\n\nExample:\n  avicore audio convert input.wav mp3",
)
@click.argument("input")
@click.argument("format")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def audio_convert(ctx: click.Context, input: str, format: str, force: bool) -> None:
    if format.lower() not in AUDIO_FORMATS:
        raise click.ClickException("Unsupported audio format")

    src = Path(input)
    if not src.exists():
        raise click.ClickException(f"Input not found: {src}")

    src_ext = src.suffix.lower().lstrip(".")
    target_format = format.lower().strip().lstrip(".")
    if src_ext == target_format:
        raise click.ClickException(
            f"Error: Cannot convert '{src.name}' to {format.upper()}. Source and target formats are identical (.{src_ext})."  # noqa: E501
        )

    dst = src.with_name(src.stem + "." + format)
    if dst.exists() and not force:
        dst = suggest_path(dst)

    temp_output = dst.with_name(dst.stem + "_aud_tmp" + dst.suffix)
    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    cmd = [str(ffmpeg), "-y", "-i", str(src), str(temp_output)]

    if run_ffmpeg(cmd, dry_run):
        src_info = probe_media_file(src, ffmpeg)
        success, _err_msg = commit_two_phase_output(
            temp_output=temp_output,
            final_dst=dst,
            src=src,
            src_info=src_info,
            ffmpeg_path=ffmpeg,
            do_backup=True,
            dry_run=dry_run,
        )
        if success:
            CREATED_FILES.append(dst)
            click.secho(f"Converted -> {dst}", fg="green")


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    cli()

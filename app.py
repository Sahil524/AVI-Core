from __future__ import annotations

import sys
import os
import signal
import subprocess
import logging
from pathlib import Path
from typing import List, Iterable, Optional, Tuple
import click
import glob

IMAGE_FORMATS = {"jpg","jpeg","png","webp","bmp"}
VIDEO_FORMATS = {"mp4","mkv","mov","avi","webm","m4v","flv","ts"}
AUDIO_FORMATS = {"mp3","wav","aac","flac","ogg"}

# ============================================================
# Version
# ============================================================

APP_VERSION: str = "1.1.0"

# ============================================================
# Globals / State
# ============================================================

CREATED_FILES: List[Path] = []
LOG_FILE: Path = Path("avicore.log")

# ============================================================
# Logging
# ============================================================

def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(message)s",
        filemode="a",
    )

# ============================================================
# FFmpeg Resolution & Verification
# ============================================================

def resolve_ffmpeg() -> Path:
    # Add the .exe extension if we are on Windows
    ext = ".exe" if os.name == "nt" else ""
    
    if hasattr(sys, "_MEIPASS"):
        # Look for ffmpeg.exe inside the temp bundle
        candidate = Path(sys._MEIPASS) / f"ffmpeg{ext}"
    else:
        # Look for ffmpeg.exe in your local bin folder
        candidate = Path(__file__).parent / "bin" / f"ffmpeg{ext}"

    return candidate


def verify_ffmpeg(ffmpeg: Path) -> None:
    if not ffmpeg.exists():
        raise click.ClickException(
            f"FFmpeg not found.\nExpected location: {ffmpeg.resolve()}"
        )

    try:
        result = subprocess.run(
            [str(ffmpeg), "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
    except Exception as exc:
        raise click.ClickException(
            "FFmpeg self-diagnostic failed.\n"
            f"Binary path: {ffmpeg.resolve()}\n"
            f"Reason: {exc}"
        )

# ============================================================
# Safety & Cleanup
# ============================================================

def register_cleanup() -> None:
    def _handler(sig, frame=None):
        click.secho("\nInterrupted. Cleaning up partial outputs…", fg="yellow")
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

def backup_original(src: Path) -> Path:
    backup_dir = src.parent / "backup"
    backup_dir.mkdir(exist_ok=True)

    target = backup_dir / src.name

    counter = 1
    while target.exists():
        target = backup_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    src.rename(target)
    return target

# ============================================================
# Subprocess Wrapper
# ============================================================

def run_ffmpeg(cmd: List[str], dry_run: bool = False) -> bool:
    logging.debug("FFmpeg cmd: %s", " ".join(cmd))

    if dry_run:
        click.secho("[DRY-RUN] " + " ".join(cmd), fg="cyan")
        return True

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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

def expand_inputs(inputs) -> List[Path]:
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

@click.group(context_settings=dict(help_option_names=[]))
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
# VERSION
# ============================================================

@cli.command(help="Display avicore version.")
def version() -> None:
    click.secho(f"avicore v{APP_VERSION}", fg="green")

@cli.command()
def help():
    click.echo("""
AVI CORE — Simple Media Toolkit

USAGE:

  avicore image convert <files> <format>
  avicore image compress <files>

  avicore video convert <files> <format>
  avicore video mute <files>

  avicore audio convert <files> <format>
  avicore audio extract <video>

EXAMPLES:

 Convert all PNG to WEBP:
   avicore image convert "*.png" webp

 Compress all JPG images:
   avicore image compress "*.jpg"

 Convert all MKV videos:
   avicore video convert "*.mkv" mp4

 Remove audio from videos:
   avicore video mute "*.mp4"

 Extract MP3 from video:
   avicore audio extract movie.mp4

GLOBAL OPTIONS:

 --dry-run     Preview operations
 --verbose     Debug logging

IMPORTANT:

 • Original files are always moved to ./backup
 • Output files keep original names
 • Wildcards must be quoted on Windows

""")


# ============================================================
# VIDEO
# ============================================================

@cli.group()
def video(): pass

@video.command(help="Universal video convert (container-aware + codec-safe).")
@click.argument("input", nargs=-1)
@click.argument("format")
@click.option("--fast", is_flag=True, help="Attempt stream copy first.")
@click.option("--force", is_flag=True, help="Overwrite if output exists.")
@click.pass_context
def convert(ctx: click.Context, input: str, format: str, fast: bool, force: bool) -> None:

    format = format.lower().strip().lstrip(".")
    if not format.isalnum() or format not in VIDEO_FORMATS:
        raise click.ClickException(f"Unsupported video format: {format}")

    files = expand_inputs(input)
    if not files:
        raise click.ClickException("No input files resolved")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    # ---- Container-aware codec matrix ----
    container_map = {
        "mkv":  {"v": "libx264",     "a": "aac", "s": "copy"},
        "mp4":  {"v": "libx264",     "a": "aac", "s": "mov_text"},
        "m4v":  {"v": "libx264",     "a": "aac", "s": "mov_text"},
        "mov":  {"v": "libx264",     "a": "aac", "s": "mov_text"},
        "webm": {"v": "libvpx-vp9",  "a": "libopus", "s": None},
        "avi":  {"v": "libxvid",     "a": "libmp3lame", "s": None},
        "flv":  {"v": "libx264",     "a": "aac", "s": None},
        "ts":   {"v": "libx264",     "a": "aac", "s": None},
    }

    ok = fail = 0

    with click.progressbar(files, label="Converting videos") as bar:
        for src in bar:

            if not src.exists() or not src.is_file():
                logging.warning("Invalid source: %s", src)
                fail += 1
                continue

            dst = src.with_name(src.stem + "." + format)

            if dst.exists():
                if not force:
                    click.secho(f"Skipping existing file: {dst.name}", fg="yellow")
                    fail += 1
                    continue
                dst.unlink(missing_ok=True)

            temp_output = dst.with_name(dst.stem + "_tmp" + dst.suffix)

            # ---------- STREAM COPY ATTEMPT ----------
            if fast:
                copy_cmd = [
                    str(ffmpeg), "-y",
                    "-i", str(src),
                    "-map", "0",
                    "-c", "copy",
                    str(temp_output),
                ]
                if run_ffmpeg(copy_cmd, dry_run):
                    try:
                        backup_original(src)
                        temp_output.replace(dst)
                        CREATED_FILES.append(dst)
                        ok += 1
                        continue
                    except Exception:
                        logging.exception("Finalize failure (copy)")
                        fail += 1
                        continue
                else:
                    temp_output.unlink(missing_ok=True)

            # ---------- UNIVERSAL ENCODE ----------
            if format in container_map:
                vcodec = container_map[format]["v"]
                acodec = container_map[format]["a"]
            else:
                vcodec = "libx264"
                acodec = "aac"

            encode_cmd = [
                str(ffmpeg), "-y",
                "-i", str(src),
                "-map", "0:v:0?",
                "-map", "0:a:0?",
                "-c:a", acodec,
                "-map", "0:s:0?",
                "-map_metadata", "0",
                "-c:v", vcodec,
                "-pix_fmt", "yuv420p",
                "-fps_mode", "passthrough",
                "-color_primaries", "bt709",
                "-color_trc", "bt709",
                "-colorspace", "bt709",
            ]

            if vcodec == "libx264":
                encode_cmd += ["-profile:v", "high", "-level", "4.1"]

            if format == "webm":
                encode_cmd = [
                    str(ffmpeg), "-y",
                    "-i", str(src),
                    "-map", "0:v:0?",
                    "-map", "0:a:0?",
                    "-c:v", vcodec,
                    "-row-mt", "1",
                    "-deadline", "good",
                    "-pix_fmt", "yuv420p",
                    "-color_primaries", "bt709",
                    "-color_trc", "bt709",
                    "-colorspace", "bt709",
                    "-fps_mode", "passthrough",
                    "-c:a", acodec,
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                ]
            else:
                encode_cmd += ["-ac", "2", "-ar", "48000"]
            
            if format in {"mp4", "mov", "m4v"}:
                encode_cmd += ["-movflags", "+faststart", "-c:s", "mov_text"]
            elif format == "mkv":
                encode_cmd += ["-c:s", "copy"]
            else:
                encode_cmd += ["-sn"]

            encode_cmd += [
                "-dn",
                "-max_muxing_queue_size", "4096",
                str(temp_output),
            ]

            if run_ffmpeg(encode_cmd, dry_run):
                try:
                    backup_original(src)
                    temp_output.replace(dst)
                    CREATED_FILES.append(dst)
                    ok += 1
                except Exception:
                    logging.exception("Finalize failure (encode)")
                    temp_output.unlink(missing_ok=True)
                    fail += 1
            else:
                temp_output.unlink(missing_ok=True)
                fail += 1

    click.secho(f"Completed → Success: {ok} | Failed: {fail}", fg="green")

@video.command(help="Universal mute (removes all audio streams safely).")
@click.argument("input", nargs=-1)
@click.option("--force", is_flag=True, help="Overwrite if output exists.")
@click.pass_context
def mute(ctx: click.Context, input: str, force: bool) -> None:

    files = expand_inputs(input)
    if not files:
        raise click.ClickException("No input files resolved")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    dry_run = ctx.obj["dry_run"]

    ok = fail = 0

    with click.progressbar(files, label="Muting videos") as bar:
        for src in bar:

            if not src.exists() or not src.is_file():
                logging.warning("Invalid source: %s", src)
                fail += 1
                continue

            dst = src
            temp_output = src.with_name(src.stem + "_muted_tmp" + src.suffix)

            if dst.exists() and not force:
                click.secho(f"Use --force to overwrite: {dst.name}", fg="yellow")
                fail += 1
                continue

            temp_output.unlink(missing_ok=True)

            cmd = [
                str(ffmpeg), "-y",
                "-i", str(src),
                "-map", "0:v?",
                "-map", "0:s?",
                "-map_metadata", "0",
                "-c", "copy",
                "-an",
                "-max_muxing_queue_size", "4096",
                str(temp_output),
            ]

            if run_ffmpeg(cmd, dry_run):
                try:
                    backup_original(src)
                    temp_output.replace(dst)
                    CREATED_FILES.append(dst)
                    ok += 1
                except Exception:
                    logging.exception("Finalize failure (mute)")
                    temp_output.unlink(missing_ok=True)
                    fail += 1
            else:
                temp_output.unlink(missing_ok=True)
                fail += 1

    click.secho(f"Completed → Success: {ok} | Failed: {fail}", fg="green")


# ============================================================
# IMAGE
# ============================================================


@cli.group()
def image(): pass


@image.command(help="Convert image(s).\nExample:\n avicore image convert *.png webp")
@click.argument("pattern", nargs=-1)
@click.argument("format")
@click.option("--force", is_flag=True)
@click.pass_context
def convert(ctx, pattern, format, force):
    import subprocess
    from pathlib import Path

    if not pattern:
        raise click.ClickException("At least one input pattern must be provided.")

    # Normalize and sanitize format
    target_format = format.strip().lower().lstrip(".")
    if not target_format.isalnum():
        raise click.ClickException("Invalid format specified.")

    files = expand_inputs(pattern)
    if not files:
        raise click.ClickException("No input files resolved.")

    # Validate source files defensively
    valid_sources = []
    for f in files:
        if not isinstance(f, Path):
            f = Path(f)

        if not f.exists():
            click.secho(f"Skipping missing file: {f}", fg="yellow")
            continue

        if not f.is_file():
            click.secho(f"Skipping non-file: {f}", fg="yellow")
            continue

        valid_sources.append(f)

    if not valid_sources:
        raise click.ClickException("No valid input files found.")

    ffmpeg = ctx.obj.get("ffmpeg")
    dry_run = ctx.obj.get("dry_run", False)

    if not ffmpeg or not Path(ffmpeg).exists():
        raise click.ClickException("Invalid ffmpeg binary configured.")

    # Dynamically validate encoder support (prevents false 'unsupported format' failures)
    try:
        result = subprocess.run(
            [str(ffmpeg), "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        encoder_list = result.stdout.lower()
        if target_format not in encoder_list:
            raise click.ClickException(
                f"Target format '{target_format}' is not supported by your ffmpeg build."
            )
    except subprocess.SubprocessError as e:
        raise click.ClickException(f"Failed to validate ffmpeg encoders: {e}")

    ok = 0
    fail = 0

    with click.progressbar(valid_sources, label="Converting images") as bar:
        for src in bar:
            try:
                dst = src.with_suffix(f".{target_format}")

                if dst.exists() and not force:
                    dst = suggest_path(dst)

                cmd = [
                    str(ffmpeg),
                    "-y" if force else "-n",
                    "-i", str(src),
                    str(dst),
                ]

                if run_ffmpeg(cmd, dry_run):
                    backup_original(src)
                    CREATED_FILES.append(dst)
                    ok += 1
                else:
                    fail += 1

            except Exception as ex:
                click.secho(f"Failed: {src} → {ex}", fg="red")
                fail += 1

    click.secho(f"Completed → Success: {ok} | Failed: {fail}", fg="green" if ok else "yellow")


@image.command(help="Compress images intelligently.\nExample:\n avicore image compress *.jpg --quality 70")
@click.argument("pattern", nargs=-1)
@click.option("--quality", default=60, show_default=True)
@click.option("--force", is_flag=True)
@click.pass_context
def compress(ctx: click.Context, pattern: str, quality: int, force: bool) -> None:
    files = expand_inputs(pattern)
    if not files:
        raise click.ClickException("No input files resolved.")

    ffmpeg: Path = ctx.obj["ffmpeg"]
    ok = 0
    fail = 0

    with click.progressbar(files, label="Compressing images") as bar:
        for src in bar:
            try:
                ext = src.suffix.lower()
                dst = src
                if dst.exists() and not force:
                    dst = suggest_path(dst)

                if ext == ".png":
                    cmd = [
                        str(ffmpeg), "-i", str(src),
                        "-compression_level", "9",
                        str(dst),
                    ]
                else:
                    q = max(2, min(31, int((100 - quality) / 3)))
                    cmd = [
                        str(ffmpeg), "-i", str(src),
                        "-q:v", str(q),
                        str(dst),
                    ]

                if run_ffmpeg(cmd, ctx.obj["dry_run"]):
                    backup_original(src)
                    CREATED_FILES.append(dst)
                    ok += 1
                else:
                    fail += 1
            except Exception:
                logging.exception("Image compress failure")
                fail += 1

    click.secho(f"Batch Report → Success: {ok}, Failed: {fail}", fg="yellow")


# ============================================================
# AUDIO COMMANDS
# ============================================================

@cli.group()
def audio(): pass

@audio.command(help="Extract audio from video as MP3 (192kbps).\n\nExample:\n  avicore audio extract input.mp4")
@click.argument("input")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def extract(ctx: click.Context, input: str, force: bool) -> None:
    src = Path(input)
    if not src.exists():
        raise click.ClickException(f"Input not found: {src}")

    dst = src.with_suffix(".mp3")
    if dst.exists() and not force:
        dst = suggest_path(dst)

    ffmpeg: Path = ctx.obj["ffmpeg"]

    # -vn = no video, -ab 192k = audio bitrate
    cmd = [
        str(ffmpeg), "-i", str(src),
        "-vn", "-ab", "192k", "-map", "a",
        str(dst)
    ]

    if run_ffmpeg(cmd, ctx.obj["dry_run"]):
        backup_original(src)
        CREATED_FILES.append(dst)
        click.secho(f"Extracted → {dst}", fg="green")

@audio.command(help="Convert audio format.\n\nExample:\n  avicore audio convert input.wav mp3")
@click.argument("input")
@click.argument("format")
@click.option("--force", is_flag=True, help="Overwrite existing files.")
@click.pass_context
def convert(ctx: click.Context, input: str, format: str, force: bool) -> None:
    if format.lower() not in AUDIO_FORMATS:
        raise click.ClickException("Unsupported audio format")

    src = Path(input)
    if not src.exists():
        raise click.ClickException(f"Input not found: {src}")

    dst = src.with_name(src.stem + "." + format)
    if dst.exists() and not force:
        dst = suggest_path(dst)

    ffmpeg: Path = ctx.obj["ffmpeg"]
    cmd = [str(ffmpeg), "-i", str(src), str(dst)]

    if run_ffmpeg(cmd, ctx.obj["dry_run"]):
        backup_original(src)
        CREATED_FILES.append(dst)
        click.secho(f"Converted → {dst}", fg="green")

# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    cli()
# AVI Core Command-Line Interface (CLI) Manual

This document provides complete reference documentation for the `avicore` command-line interface.

---

## 1. Access & Execution

Once installed, the CLI executable `avicore` is accessible from any Command Prompt or PowerShell terminal.

```text
# Standalone binary (Installed)
avicore [GLOBAL_OPTIONS] COMMAND [ARGS]...

# Development environment
python app.py [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

---

## 2. Global Options

These options apply across all top-level subcommands and groups:

| Flag | Description |
| :--- | :--- |
| `-h`, `--help` | Display command usage, available options, and subcommands. |
| `--verbose` | Enable verbose debug logging to `avicore.log` in the working directory. |
| `--dry-run` | Simulate operations. Generates and prints the exact FFmpeg command array without performing disk writes. |

---

## 3. General Commands

### 3.1 `avicore version`
Prints the current release version of the application.

```powershell
avicore version
```
**Output:**
```text
avicore v2.0.0
```

### 3.2 `avicore help`
Prints an operational cheat sheet summarizing common command invocations.

```powershell
avicore help
```

---

## 4. Video Commands (`avicore video`)

### 4.1 `avicore video convert`
Converts one or more video files into the target format.

```text
avicore video convert [OPTIONS] INPUT... FORMAT
```

#### Arguments:
* `INPUT...`: One or more input file paths, or wildcard patterns (e.g. `recording.mkv`, `*.mov`, `"part 1.avi"`).
* `FORMAT`: Target video container (`mp4`, `mkv`, `mov`, `avi`, `webm`, `m4v`, `flv`, `ts`).

#### Options:
* `--fast`: **Fast Stream Copy.** Attempts direct container repackaging without re-encoding video/audio streams when codecs are compatible. Conversion completes in ~1-2 seconds with zero generational loss.
* `--force`: Overwrites destination files if they already exist. By default, existing files are skipped.

#### Examples:
```powershell
# Remux MKV to MP4 without re-encoding (instant stream copy)
avicore video convert movie.mkv mp4 --fast

# Convert QuickTime MOV to MP4 with hardware acceleration
avicore video convert sample.mov mp4

# Batch convert all AVI files in the current folder to WebM
avicore video convert *.avi webm

# Force overwrite of existing MP4 destination
avicore video convert clip.mkv mp4 --force
```

---

### 4.2 `avicore video mute`
Creates a copy of the video with all audio streams stripped. Video streams, subtitle tracks, and metadata are preserved.

```text
avicore video mute [OPTIONS] INPUT...
```

#### Arguments:
* `INPUT...`: One or more video files.

#### Options:
* `--force`: Overwrites the original input file in-place instead of creating a `<name>_muted.<ext>` file.

#### Examples:
```powershell
# Mute a single video (creates clip_muted.mp4)
avicore video mute clip.mp4

# Mute all MP4 files in a directory
avicore video mute *.mp4
```

---

## 5. Audio Commands (`avicore audio`)

### 5.1 `avicore audio convert`
Transcodes a single audio file between supported audio formats.

```text
avicore audio convert [OPTIONS] INPUT FORMAT
```

#### Arguments:
* `INPUT`: Source audio file path.
* `FORMAT`: Target audio format (`mp3`, `wav`, `aac`, `flac`, `ogg`, `m4a`).

#### Options:
* `--force`: Overwrites destination file if it already exists.

#### Examples:
```powershell
# Convert uncompressed WAV to 320kbps MP3
avicore audio convert recording.wav mp3

# Convert FLAC to Apple Lossless / AAC container
avicore audio convert master.flac m4a
```

---

### 5.2 `avicore audio extract`
Extracts the primary audio soundtrack from a video file.

```text
avicore audio extract [OPTIONS] INPUT
```

#### Arguments:
* `INPUT`: Video file path containing audio streams.

#### Behavior:
* If the source audio stream codec matches a native format (e.g. AAC, MP3, Opus, FLAC), it is copied directly without transcoding into the appropriate extension (`.m4a`, `.mp3`, `.opus`, `.flac`).
* If the codec is incompatible with direct extraction, it is transcoded to high-quality MP3 (`192k`).

#### Examples:
```powershell
# Extract audio from a video recording
avicore audio extract conference.mp4

# Extract audio and overwrite if destination exists
avicore audio extract gameplay.mkv --force
```

---

## 6. Image Commands (`avicore image`)

### 6.1 `avicore image convert`
Converts one or more image files between formats.

```text
avicore image convert [OPTIONS] PATTERN... FORMAT
```

#### Arguments:
* `PATTERN...`: One or more image file paths, or wildcard patterns (`*.png`, `photo.jpg`).
* `FORMAT`: Target image format (`jpg`, `jpeg`, `png`, `webp`, `bmp`).

#### Behavior:
* Converting transparent images (PNG, WebP with alpha) to JPEG automatically applies a white matte background composite to prevent black artifacting.
* WebP defaults to quality factor 90. JPEG defaults to high quality `-q:v 2`.

#### Examples:
```powershell
# Convert a single PNG image to WebP
avicore image convert photo.png webp

# Batch convert all PNG images in current directory to WebP
avicore image convert *.png webp

# Convert WebP back to PNG
avicore image convert graphic.webp png
```

---

### 6.2 `avicore image compress`
Compresses image files to optimize disk storage while maintaining visual fidelity.

```text
avicore image compress [OPTIONS] PATTERN...
```

#### Options:
* `--quality INT`: Quality level from 1 to 100 (Default: `60`). Applies to lossy formats like JPEG and WebP.
* `--force`: Overwrites the file in place. If omitted, creates `<name>_comp.<ext>` or suggests an incremental name.

#### Behavior:
* **PNG:** Applies maximum lossless DEFLATE compression (`-compression_level 9`).
* **JPEG / WebP:** Dynamically scales quantization factors according to the `--quality` parameter.

#### Examples:
```powershell
# Compress a large JPEG photo to 75% quality
avicore image compress wallpaper.jpg --quality 75

# Compress all PNG files losslessly
avicore image compress *.png
```

---

## 7. Management & Diagnostics Commands

### 7.1 `avicore menu install`
Registers the cascading Windows Explorer right-click context menu for all 19 supported media file extensions.

```powershell
avicore menu install
```

### 7.2 `avicore menu remove`
Unregisters and cleans all Windows Explorer context menu entries from the Windows registry.

```powershell
avicore menu remove
```

### 7.3 `avicore system diagnostics`
Generates a comprehensive diagnostic ZIP support bundle containing FFmpeg version output, GPU hardware encoder capabilities, operating system specifications, and recent log files.

```powershell
avicore system diagnostics
```
**Output:**
```text
Diagnostic bundle generated successfully: avicore_diagnostics_20260930_193000.zip
```

---

## 8. Exit Codes & Signal Handling

AVI Core returns standardized process exit codes for integration into CI/CD pipelines and scripts:

| Exit Code | Meaning |
| :--- | :--- |
| `0` | Success. All input files processed successfully. |
| `1` | Error. Validation failure, unsupported format, or encoding failure. |
| `130` | Interrupted. The process received `SIGINT` (Ctrl+C). Active in-flight `.tmp` files are cleaned up automatically. |

### Signal Interruption Safety:
When interrupted via `Ctrl+C`:
1. The signal handler immediately traps `SIGINT`.
2. All temporary staging files registered in `CREATED_FILES` are unlinked.
3. The process exits with code `130` without leaving corrupt, half-written media files on disk.

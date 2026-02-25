# Avicore: Universal Media CLI

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

**Avicore** is a hardened, production-grade command-line tool for processing media. It wraps the complexity of FFmpeg into simple, human-readable commands. It handles video, audio, and image processing with defensive safety checks, smart file naming, and detailed progress reporting.

---

## ⚡ Quick Install (Windows)

You do not need Python or FFmpeg installed. Avicore is standalone.

### Step 1: Download
Download the latest `avicore.exe` from the [Releases Page](https://github.com/Sahil524/avicore/releases).

### Step 2: Install (Add to Path)
1.  Place `avicore.exe` in a permanent folder (e.g., inside `Documents` or `C:\Tools`).
2.  Open **PowerShell** in that folder (Shift + Right Click > "Open PowerShell window here").
3.  Copy and run this command to make Avicore available everywhere:

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";" + (Get-Location), "User")
```
That's it! Close PowerShell and open a new terminal. You can now type avicore from anywhere.

# 📖 Command Reference

---

## 🎬 Video

Supported formats: `mp4` `mkv` `mov` `avi` `webm` `m4v` `flv` `ts`

### Convert

Re-encodes a video to a new format using H.264/AAC for broad compatibility.

```bash
avicore video convert [FILE] [FORMAT]
```

```bash
# Single file
avicore video convert movie.mkv mp4

# Batch (quote the pattern on Windows)
avicore video convert "*.mov" mp4

# Stream copy — instant, but only works if codecs are already compatible
avicore video convert movie.mkv mp4 --fast

# Overwrite existing output file
avicore video convert movie.mkv mp4 --force
```

> **`--fast`** skips re-encoding and just remuxes the container. Much faster, but will silently fall back to full encoding if codecs are incompatible.

---

### Mute

Strips the audio track. Video and subtitles are stream-copied (no re-encoding, instant).

```bash
avicore video mute [FILE]
```

```bash
# Single file
avicore video mute clip.mp4

# Batch
avicore video mute "*.mp4"

# Overwrite original
avicore video mute clip.mp4 --force
```

---

## 🎵 Audio

Supported formats: `mp3` `wav` `aac` `flac` `ogg`

### Extract

Pulls the audio track from a video and saves it as a 192kbps MP3.

```bash
avicore audio extract [VIDEO_FILE]
```

```bash
avicore audio extract lecture.mp4
# Output: lecture.mp3

avicore audio extract lecture.mp4 --force   # overwrite if lecture.mp3 exists
```

---

### Convert

Converts an audio file to a different format.

```bash
avicore audio convert [FILE] [FORMAT]
```

```bash
avicore audio convert recording.wav mp3
avicore audio convert podcast.flac aac --force
```

---

## 🖼️ Image

Supported formats: `jpg` `jpeg` `png` `webp` `bmp`

### Compress

Reduces file size. Behaviour differs by type:

- **JPG / WEBP** — adjusts quality factor (lossy). Default quality: `60`.
- **PNG** — sets compression level to maximum (lossless, no quality loss).

```bash
avicore image compress [PATTERN] --quality [0–100]
```

```bash
# Compress all JPGs at default quality (60)
avicore image compress "*.jpg"

# Lower quality = smaller file
avicore image compress "*.jpg" --quality 40

# Overwrite originals
avicore image compress "*.jpg" --force
```

---

### Convert

Changes an image to a different format.

```bash
avicore image convert [PATTERN] [FORMAT]
```

```bash
# Single file
avicore image convert logo.png webp

# Batch
avicore image convert "*.png" webp

# Overwrite existing output files
avicore image convert "*.png" webp --force
```

---

## ⚙️ Global Options

These flags work with any command.

| Flag | Effect |
|------|--------|
| `--dry-run` | Prints the FFmpeg commands without running them. Safe way to preview what will happen. |
| `--verbose` | Writes detailed FFmpeg output to `avicore.log` in the current folder. Use this when a file fails. |

```bash
# Preview a batch conversion without touching any files
avicore --dry-run video convert "*.mkv" mp4

# Debug a failing conversion
avicore --verbose video convert broken.mp4 mp4
```

---

## 🛡️ File Safety

- **Originals are always backed up.** Before any operation, the source file is moved to a `./backup/` folder in the same directory. Nothing is deleted.
- **Overwrite protection is on by default.** If the output file already exists, avicore renames the new file (e.g. `video_1.mp4`) instead of overwriting. Use `--force` to override this.
- **Partial files are cleaned up automatically.** If you cancel with `Ctrl+C`, any incomplete output file is deleted.

---

## 🛠️ Build from Source

For developers who want to modify or package avicore.

**1. Clone the repo**
```bash
git clone https://github.com/Sahil524/avicore
```

**2. Install dependencies**
```bash
pip install click pyinstaller
```

**3. Add the FFmpeg engine**

Download a static FFmpeg binary from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extract `ffmpeg.exe`, and place it at:
```
avicore/
└── bin/
    └── ffmpeg.exe
```

**4. Build**
```bash
python -m PyInstaller --onefile --add-binary "bin/ffmpeg.exe;." --name avicore --clean app.py
```

The final binary will be at `dist/avicore.exe`.
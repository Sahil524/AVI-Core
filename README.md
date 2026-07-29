# AVI Core: Universal Media Processing Engine

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

**AVI Core** is a hardened, production-grade command-line tool and Windows Explorer context menu media processing platform. It wraps FFmpeg into intelligent, human-readable commands for video, audio, and image processing with zero-data-loss two-phase atomic commits, dynamic GPU acceleration, and container-aware metadata rules.

---

## ⚡ Features & Capabilities

- **Intelligent Media Probing**: Media-aware stream analysis (`ffprobe`) preventing color distortion on HDR content and audio stream drops.
- **Hardware Acceleration**: Automatic GPU encoder detection and fallback chain (`NVENC` ➔ `QSV` ➔ `AMF` ➔ `CPU`).
- **Two-Phase Atomic Commit**: Encodes to `.tmp_output`, verifies stream integrity and duration parity, and safely moves originals to `./backup/`.
- **Conversion Profiles Engine**: Built-in presets for YouTube, Instagram, TikTok, Discord, WhatsApp, Lossless Archival, and Web Optimization.
- **Container-Aware Metadata Engine**: Preserves EXIF, ICC profiles, GPS, chapters, and cover art according to target container capability.
- **Zero-Daemon Batch Execution**: Parallel worker scheduling throttled dynamically by CPU and RAM resource monitoring.
- **Diagnostics Framework**: Single-command diagnostic bundle ZIP generator (`avicore system diagnostics`).

---

## 📖 Command Reference

### 🎬 Video Commands
```bash
# Convert video to MP4 (auto-detects NVENC / QSV / AMF GPU hardware)
avicore video convert movie.mkv mp4

# Stream copy (instant container remuxing without re-encoding)
avicore video convert clip.mkv mp4 --fast

# Mute video (removes audio streams safely without quality loss)
avicore video mute clip.mp4
```

### 🖼️ Image Commands
```bash
# Convert PNG image to WebP format
avicore image convert logo.png webp

# Compress JPG image at specified quality factor (default: 60)
avicore image compress "*.jpg" --quality 75
```

### 🎵 Audio Commands
```bash
# Extract 192kbps MP3 audio from video
avicore audio extract lecture.mp4

# Convert audio format
avicore audio convert recording.wav mp3
```

### ⚙️ Diagnostics & Global Flags
```bash
# Generate a ZIP support bundle containing system specs and logs
avicore system diagnostics

# Preview commands without executing
avicore --dry-run video convert clip.mkv mp4

# Enable verbose logging
avicore --verbose video convert clip.mkv mp4
```

---

## 🛠️ Build from Source

```bash
git clone https://github.com/Sahil524/avicore.git
cd avicore
pip install -r requirements.txt pyinstaller
powershell -ExecutionPolicy Bypass -File build_binaries.ps1
```

The final output executables will be generated at `dist/avicore/avicore.exe` and `dist/context_menu.exe`.

---

## 📄 License
MIT License.
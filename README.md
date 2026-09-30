# AVI Core — Open-Source Offline Media Converter for Windows

<p align="center">
  <img src="logo.webp" alt="AVI Core Logo" width="140" />
</p>

<p align="center">
  <strong>Fast, private media conversion directly from your Windows right-click menu or command line.</strong><br />
  Powered by an internal hardware-accelerated FFmpeg engine. 100% offline. Zero cloud uploads. Zero tracking. Free forever under the MIT license.
</p>

<p align="center">
  <a href="https://github.com/Sahil524/AVI-Core/releases/latest"><img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version 2.0.0" /></a>
  <a href="https://github.com/Sahil524/AVI-Core"><img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-lightgrey.svg" alt="Windows 10 & 11" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License" /></a>
  <a href="https://sahil524.github.io/AVI-Core/"><img src="https://img.shields.io/badge/website-online-gold.svg" alt="Official Website" /></a>
</p>

---

## 📌 What is AVI Core?

**AVI Core** (also known as `AVI-Core` or `AVICORE`) is an open-source, local-first media conversion engine designed for Windows 10 and 11. It eliminates the frustration of ad-infested web converters and confusing command-line tools by embedding powerful conversion capabilities directly into your **Windows File Explorer right-click context menu** and providing a clean, scriptable **developer CLI** (`avicore`).

### The Problems AVI Core Solves:
1. **Privacy Invasions:** Online converters force you to upload personal photos, podcasts, and recordings to unknown third-party servers. AVI Core runs **100% locally on your CPU/GPU**—zero network requests, zero telemetry, zero data leaves your PC.
2. **Artificial File Size & Speed Limits:** Web converters cap file sizes at 50MB–100MB and artificially throttle processing speeds behind paid subscriptions. AVI Core converts multi-gigabyte 4K and 8K videos at maximum hardware speed.
3. **Accidental File Loss:** Media tools often overwrite master recordings when converting. AVI Core automatically vaults raw source files into a `./backup/` directory before processing.
4. **Complex FFmpeg Syntax:** Memorizing complex terminal flags for pixel formats, audio downmixing, and stream mapping is error-prone. AVI Core automates optimal encoder resolution, audio channel matrices, and container compatibility.
5. **System Freezes During Bulk Conversions:** Selecting dozens of files in Explorer usually causes Windows to launch dozens of simultaneous processes. AVI Core's Win32 Named Mutex spooler consolidates Explorer launches into a single smooth queue.

---

## 🚀 Key Features

* **⚡ Fast Stream Copy (`--fast` / Fast Convert):** Repackage video containers (e.g. MKV to MP4) in 1–2 seconds with zero re-encoding, zero CPU load, and zero quality loss.
* **📂 Native Windows Explorer Context Menu:** Right-click single or multiple media files to Convert, Fast Convert, Extract Audio, Mute, or Compress.
* **🛡️ Automatic Safety Vaulting:** Originals are safely moved to `./backup/` before processing.
* **🔒 Two-Phase Atomic Commits:** Output is encoded to a `.tmp` buffer, verified with probe diagnostics (valid headers, decodable streams, duration parity), and committed atomically.
* **🚀 Hardware Acceleration:** Automatically probes and utilizes NVIDIA NVENC (`h264_nvenc`), Intel QuickSync (`h264_qsv`), or AMD AMF (`h264_amf`) with graceful CPU fallback (`libx264`).
* **💻 Clean Developer CLI (`avicore`):** Container-aware CLI supporting wildcard batching, progress reporting, ETA estimation, and `--dry-run` simulation.
* **🌐 Companion Web Converter:** In-browser converter running 100% client-side via HTML5 Canvas and Web Audio API with zero server uploads.

---

## 🌐 Official Links

* **Official Homepage:** [https://sahil524.github.io/AVI-Core/](https://sahil524.github.io/AVI-Core/)
* **In-Browser Web Converter:** [https://sahil524.github.io/AVI-Core/converter.html](https://sahil524.github.io/AVI-Core/converter.html)
* **Official Downloads:** [https://sahil524.github.io/AVI-Core/download.html](https://sahil524.github.io/AVI-Core/download.html)
* **GitHub Repository:** [https://github.com/Sahil524/AVI-Core](https://github.com/Sahil524/AVI-Core)
* **Latest Releases:** [https://github.com/Sahil524/AVI-Core/releases](https://github.com/Sahil524/AVI-Core/releases)

---

## 📚 Detailed Documentation

Detailed technical and user documentation is maintained in the [`docs/`](docs/) directory:

| Document | Description |
| :--- | :--- |
| [**Architecture & System Design**](docs/ARCHITECTURE.md) | Component architecture, lifecycle diagrams, mutex spooling, and safety guarantees. |
| [**Installation & Deployment Guide**](docs/INSTALLATION.md) | Setup wizard, PowerShell automation, prerequisites, upgrades, and troubleshooting. |
| [**CLI Reference Manual**](docs/CLI.md) | Complete guide to all `avicore` commands, arguments, options, and exit codes. |
| [**Windows Explorer Integration**](docs/WINDOWS-EXPLORER.md) | Deep dive into right-click context menus, registry structures, and multi-selection queues. |
| [**Supported Formats Specification**](docs/SUPPORTED-FORMATS.md) | Complete list of video, audio, and image formats supported across desktop and web. |
| [**Web Converter Reference**](docs/WEB-CONVERTER.md) | Architecture of the client-side browser converter (Canvas & Web Audio API). |
| [**Developer Guide**](docs/DEVELOPMENT.md) | Environment setup, running locally, test suites, static analysis, and PyInstaller builds. |

---

## 🎯 Genuinely Supported Format Matrix

### Desktop Engine (FFmpeg-Backed)
* **Video Formats:** `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`, `.m4v`, `.flv`, `.ts`
  * *Encoders:* NVIDIA NVENC, Intel QuickSync, AMD AMF, CPU (libx264 High Profile, VP9, Xvid)
  * *Features:* Lossless Stream Copy (`--fast`), Audio Downmix to Stereo, Subtitle Passthrough (`mov_text`/`copy`)
* **Audio Formats:** `.mp3`, `.wav`, `.aac`, `.flac`, `.ogg`, `.m4a`
  * *Encoders:* libmp3lame (320kbps), 16-bit PCM WAV (48kHz), Native AAC (256kbps), FLAC lossless, Vorbis
* **Image Formats:** `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`
  * *Features:* Adaptive WebP (-quality 90), JPEG (-q:v 2), PNG Level 9 DEFLATE, White Matte Compositing for Transparency

### Web Converter (In-Browser)
* **Image Export:** `.webp` (quality slider), `.png` (lossless), `.jpg` (quality slider)
* **Audio Export:** `.wav` (16-bit uncompressed PCM via Web Audio API)
* *Note:* Video re-encoding and direct MP3 encoding require the desktop application.

---

## ⚡ Quick Start: Installation

AVI Core is fully self-contained. You do **not** need Python or FFmpeg pre-installed.

### Option 1: Setup Wizard (Inno Setup)
1. Download `AVI-Core-Setup-v2.0.0.exe` from [GitHub Releases](https://github.com/Sahil524/AVI-Core/releases/latest).
2. Run the installer wizard.
3. The installer sets up PATH and registers the Windows Explorer context menu automatically.

### Option 2: Automated PowerShell Script
For developers, portable use, or CI/CD pipelines:
```powershell
# Double-click install.bat or run in PowerShell:
powershell -ExecutionPolicy Bypass -File install.ps1
```
* Supports standard user scope (`%LOCALAPPDATA%\Programs\AVICore`) without requiring administrative elevation.
* To uninstall: run `uninstall.bat` or `powershell -ExecutionPolicy Bypass -File uninstall.ps1`.

---

## 💻 CLI Quick Usage

```powershell
# 1. Video stream copy remuxing (Lossless, ~1-2 seconds)
avicore video convert movie.mkv mp4 --fast

# 2. Hardware-accelerated video conversion
avicore video convert clip.mov mp4

# 3. Mute a video (strips audio, keeps video/subtitles)
avicore video mute presentation.mp4

# 4. Extract audio track from video
avicore audio extract lecture.mp4

# 5. Audio format conversion
avicore audio convert voice.wav mp3

# 6. Convert single image or wildcard batch to WebP
avicore image convert photo.png webp
avicore image convert *.png webp

# 7. Compress image files
avicore image compress banner.jpg --quality 75

# 8. Manage Windows Explorer right-click context menu
avicore menu install
avicore menu remove

# 9. Generate diagnostic support bundle
avicore system diagnostics
```

---

## 🛠️ Build From Source

```powershell
# 1. Clone the repository
git clone https://github.com/Sahil524/AVI-Core.git
cd "AVI Core"

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 4. Run test suite
pytest tests/ -v

# 5. Compile standalone binaries (PyInstaller)
powershell -ExecutionPolicy Bypass -File build_binaries.ps1
```
Compiled standalone executables are generated in `dist/avicore/avicore.exe` and `dist/context_menu.exe`.

---

## 🤝 Contributing

We welcome contributions! Please review [CONTRIBUTING.md](CONTRIBUTING.md) for bug reporting instructions, feature suggestions, testing expectations, and coding standards.

---

## 🛡️ Security

For vulnerability reporting procedures and security considerations, see [SECURITY.md](SECURITY.md).

---

## 📜 Version History

See [CHANGELOG.md](CHANGELOG.md) for factual release notes and historical changes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
All bundled third-party binaries (FFmpeg) are governed by their respective licenses (LGPL/GPL).
# AVI Core: Universal Media Processing Engine

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

**AVI Core** is a hardened, production-grade media processing tool that wraps the power of FFmpeg into simple, human-readable commands. It supports video, audio, and image processing through both a command-line interface and native Windows File Explorer integration, allowing you to process media directly from the right-click menu.

---

# ⚡ Quick Install (Windows)

You do not need Python or FFmpeg installed. AVI Core is completely standalone.

### Step 1: Download

Download the latest **AVI Core Installer** from the [Releases Page](https://github.com/Sahil524/avicore/releases).

### Step 2: Install

Run the installer and follow the setup wizard.

The installer automatically:

* Installs AVI Core
* Adds AVI Core to your system PATH
* Registers the Windows File Explorer context menu
* Configures the application for immediate use

That's it! After installation, you can use AVI Core directly from Command Prompt, PowerShell, Windows Terminal, or simply by right-clicking supported media files in File Explorer.

---

# 📂 Windows Explorer Context Menu

AVI Core now integrates directly with Windows File Explorer.

Simply right-click a supported media file to access AVI Core without opening a terminal.

### 🖼️ Image Files

Available actions include:

* Convert to JPG
* Convert to JPEG
* Convert to PNG
* Convert to WebP
* Convert to BMP
* Compress Image

### 🎬 Video Files

Available actions include:

* Convert Video
* Extract Audio
* Remove Audio (Mute Video)

The context menu is dynamic and displays only the operations supported for the selected file type.

---

# 📖 Command Reference

## 🎬 Video Commands

### Convert Video

Converts a video to another supported format.

**Usage**

```bash
avicore video convert [INPUT] [FORMAT]
```

**Example**

```bash
avicore video convert movie.mkv mp4
```

**Options**

* `--fast` — Uses stream copy when possible.
* `--force` — Overwrites existing files.

---

### Mute Video

Removes the audio stream while preserving the video.

```bash
avicore video mute clip.mp4
```

---

## 🎵 Audio Commands

### Extract Audio

```bash
avicore audio extract lecture.mp4
```

### Convert Audio

```bash
avicore audio convert recording.wav mp3
```

---

## 🖼️ Image Commands

### Compress Image

```bash
avicore image compress image.jpg --quality 75
```

### Convert Image

```bash
avicore image convert logo.png webp
```

---

# ⚙️ Advanced Features

## 🛡️ Safety Systems

* Smart overwrite protection
* Automatic cleanup of interrupted conversions
* Dynamic Windows Explorer context menu
* Standalone embedded FFmpeg engine
* Automatic output naming to prevent accidental overwrites

---

## 🐛 Debugging

Generate verbose logs for troubleshooting.

```bash
avicore --verbose video convert broken.mp4 mp4
```

---

# 🛠️ Build from Source

Clone the repository:

```bash
git clone https://github.com/Sahil524/avicore.git
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Build the executables:

```powershell
powershell -ExecutionPolicy Bypass -File build_binaries.ps1
```

Compiled binaries will be available in the `dist/` directory.

---

# 📄 License

This project is licensed under the MIT License.

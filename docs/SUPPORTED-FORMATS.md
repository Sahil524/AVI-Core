# AVI Core Supported Formats Specification

This document provides a factual specification of all media formats, containers, codecs, and compression options supported by AVI Core (version 2.0.0).

---

## 1. Summary Matrix: Desktop vs. Web Converter

| Media Category | Windows Desktop Engine (FFmpeg) | Web Converter (Browser) |
| :--- | :--- | :--- |
| **Video Conversion** | Full transcode & lossless stream copy across 8 containers | Not supported in browser |
| **Video Muting** | Supported across all 8 video containers | Not supported in browser |
| **Audio Extraction** | Extracts to native format or high-bitrate MP3 | Extracts audio to uncompressed 16-bit PCM WAV |
| **Audio Conversion** | Full transcode across 6 audio formats | Not supported in browser |
| **Image Conversion** | Converts between PNG, JPG, WebP, BMP with alpha compositing | Converts between WebP, PNG, JPG via HTML5 Canvas |
| **Image Compression** | Lossless DEFLATE (PNG) & adaptive quantization (JPEG/WebP) | Lossy quality adjustment slider (WebP, JPG) |

---

## 2. Desktop Application Formats (FFmpeg-Backed)

The desktop application (`avicore.exe` and context menu) supports **19 primary media formats**.

### 2.1 Video Containers & Codecs

| Container | Extension | Video Codec | Audio Codec | Subtitles | Fast Stream Copy (`--fast`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MP4** | `.mp4` | H.264 (`h264_nvenc`, `h264_qsv`, `h264_amf`, or `libx264`) | AAC (`aac`) | `mov_text` | Yes |
| **Matroska** | `.mkv` | H.264 / passthrough | AAC / passthrough | Direct copy (`copy`) | Yes |
| **QuickTime** | `.mov` | H.264 | AAC (`aac`) | `mov_text` | Yes |
| **Audio Video Interleave** | `.avi` | MPEG-4 / Xvid (`libxvid`) | MP3 (`libmp3lame`) | Stripped | Yes |
| **WebM** | `.webm` | VP9 (`libvpx-vp9`) | Opus (`libopus`) | Stripped | Yes |
| **iTunes Video** | `.m4v` | H.264 | AAC (`aac`) | `mov_text` | Yes |
| **Flash Video** | `.flv` | H.264 | AAC (`aac`) | Stripped | Yes |
| **MPEG-2 Transport Stream** | `.ts` | H.264 | AAC (`aac`) | Stripped | Yes |

#### Video Hardware Encoder Selection Chain:
When encoding H.264 video, AVI Core probes the hardware and selects the highest-performing available encoder:
1. **NVIDIA NVENC:** `h264_nvenc`
2. **Intel QuickSync:** `h264_qsv`
3. **AMD AMF:** `h264_amf`
4. **CPU Fallback:** `libx264` (High Profile, Level 4.1)

#### Fast Stream Copy (`--fast` / Fast Convert):
When the source video streams and target container are compatible (e.g. H.264 video inside an MKV container converting to MP4), the `--fast` flag executes a lossless stream copy (`-c copy`). The container metadata is remuxed in ~1–2 seconds with zero re-encoding, zero CPU load, and zero generational loss.

---

### 2.2 Audio Formats

| Format | Extension | Underlying Codec | Bitrate / Specs | Multi-Channel Handling |
| :--- | :--- | :--- | :--- | :--- |
| **MP3** | `.mp3` | `libmp3lame` | 320 kbps (transcode) / 192 kbps (extract) | Downmixed to Stereo |
| **WAV** | `.wav` | `pcm_s16le` | 16-bit uncompressed PCM, 48 kHz | Downmixed to Stereo |
| **AAC** | `.aac` | `aac` | 256 kbps native AAC | Downmixed to Stereo |
| **FLAC** | `.flac` | `flac` | Lossless Free Lossless Audio Codec | Preserved |
| **OGG** | `.ogg` | `libvorbis` | Ogg Vorbis standard quality | Downmixed to Stereo |
| **M4A** | `.m4a` | `aac` / `alac` | MPEG-4 Audio Container | Downmixed to Stereo |

#### Audio Downmix Matrix:
When 5.1 or 7.1 surround sound audio is converted to stereo, AVI Core applies ITU-R BS.775 channel downmixing:
```text
pan=stereo|FL=0.5*FC+0.707*FL+0.707*BL|FR=0.5*FC+0.707*FR+0.707*BR
```
This ensures center dialogue and surround ambient tracks are evenly blended into left and right stereo channels without acoustic clipping.

---

### 2.3 Image Formats

| Format | Extension | Capabilities | Transparency Handling |
| :--- | :--- | :--- | :--- |
| **JPEG** | `.jpg`, `.jpeg` | High-quality quantization (`-q:v 2`) | Automatic white background compositing (`split...overlay`) |
| **PNG** | `.png` | Lossless DEFLATE Level 9 (`-compression_level 9`) | Full Alpha Channel Preserved |
| **WebP** | `.webp` | High-efficiency adaptive WebP (`-quality 90`) | Full Alpha Channel Preserved |
| **BMP** | `.bmp` | Windows uncompressed bitmap | Stripped to RGB |

---

## 3. Web Converter Formats (`converter.html`)

The Web Converter operates 100% inside the user's browser using native Web APIs without uploading files or relying on WebAssembly FFmpeg.

### 3.1 Web Input Formats
* **Images:** Any image format decodable by the client browser's `Image()` engine (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`).
* **Audio & Video:** Any media file decodable by the browser's `AudioContext.decodeAudioData()` (`.mp3`, `.wav`, `.ogg`, `.aac`, `.m4a`, `.mp4`, `.webm`).

### 3.2 Web Output Formats

| Target Format | Implementation Engine | Adjustable Options | Output Container |
| :--- | :--- | :--- | :--- |
| **.webp** | HTML5 Canvas `canvas.toBlob('image/webp', quality)` | Quality slider (1% – 100%) | Standard WebP Image |
| **.png** | HTML5 Canvas `canvas.toBlob('image/png')` | Lossless | Standard PNG Image |
| **.jpg** | HTML5 Canvas `canvas.toBlob('image/jpeg', quality)` | Quality slider (1% – 100%) | Standard JPEG Image |
| **.wav** | Web Audio API + Custom 16-bit PCM RIFF Binary Packer | Uncompressed | 16-bit 44.1/48kHz Stereo WAV |

### 3.3 What the Web Converter Does NOT Support:
* **Video container re-encoding:** The browser cannot encode arbitrary video into `.mp4`, `.mkv`, or `.mov`. For video conversion, use the desktop application.
* **Direct MP3 encoding:** The browser cannot encode `.mp3` without heavy external WASM libraries. Audio extraction in the browser produces standard uncompressed `.wav`.

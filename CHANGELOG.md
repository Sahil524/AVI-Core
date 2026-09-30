# Changelog

All notable changes to **AVI Core** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-09-30

### Added
* **Modular Pipeline Architecture:** Introduced the `avicore/` package with a structured, multi-stage processing lifecycle (`MediaProcessingPipeline`, `MediaInfo`, `capabilities`, `optimizer`, `rules`).
* **Hardware Acceleration Engine:** Added automatic detection and selection of GPU encoders:
  * NVIDIA NVENC (`h264_nvenc`)
  * Intel QuickSync (`h264_qsv`)
  * AMD AMF (`h264_amf`)
  * Graceful fallback to CPU (`libx264`).
* **Fast Stream Copy (`--fast` / Fast Convert):** Added instant container repackaging for compatible streams without quality loss or re-encoding.
* **Non-Destructive Storage Lifecycle:**
  * Two-phase atomic commit model writing to `<file>_tmp.<ext>` buffers.
  * Media probe verification (`verify_output_file`) verifying file existence, non-zero byte size, stream decodability, and duration parity before committing.
  * Automated master file vaulting to `./backup/` directory prior to destination replacement.
* **Windows Explorer Context Menu Debouncer:**
  * Introduced Win32 Named Mutex (`Global\AVICore_Spool_Mutex`) with a transient spool file in `%TEMP%\avicore_spool.txt`.
  * Aggregates simultaneous Explorer process invocations into a single coordinated batch execution to prevent CPU exhaustion.
* **Unified CLI (`avicore`):**
  * Re-architected CLI using Click with subcommands: `video convert`, `video mute`, `audio convert`, `audio extract`, `image convert`, `image compress`, `menu install/remove`, and `system diagnostics`.
  * Added `--dry-run` flag for command inspection without disk writes.
  * Added `--verbose` flag routing debug output to `avicore.log`.
  * Added signal handlers (`SIGINT`/`SIGTERM`) to clean up in-flight temporary files.
* **In-Browser Web Converter (`converter.html`):**
  * Added 100% client-side web converter supporting image conversion to WebP, PNG, JPG via HTML5 Canvas.
  * Added in-browser audio extraction to 16-bit uncompressed WAV via the Web Audio API.
  * Added client-side batch archiving via JSZip with zero server uploads.
* **Automated Packaging & Installers:**
  * PowerShell automated installer (`install.ps1` and `install.bat`) supporting non-elevated user scope installation (`%LOCALAPPDATA%\Programs\AVICore`).
  * Inno Setup configuration (`installer.iss`) building `AVI-Core-Setup-v2.0.0.exe`.
  * PyInstaller build script (`build_binaries.ps1`) building `dist/avicore` and `dist/context_menu.exe`.
* **Test Suite:** Added unit and integration tests using `pytest` and `pytest-cov` covering CLI invocation, hardware capabilities, optimizer passthrough, and verification logic.

### Changed
* Redesigned registry key structure under `SystemFileAssociations` instead of `ProgID` so context menus appear regardless of default media associations.
* Upgraded web documentation pages with modern responsive layouts and zero padding bugs.
* Enhanced error reporting with informative dialogs and centralized logging in `%LOCALAPPDATA%\AVICore\logs`.

---

## [1.0.0] - 2026-03-15

### Added
* Initial release of AVI Core for Windows.
* Basic command-line wrapper around FFmpeg for video and audio conversion.
* Initial Windows Explorer right-click context menu registration script.
* Bundled FFmpeg static binary.
* Basic project website and MIT open source license.

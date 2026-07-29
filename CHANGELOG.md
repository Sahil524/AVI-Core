# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-07-29

### Added
- Complete integration of parallel execution via `BatchProcessor` in the CLI commands (`convert`, `mute`, `compress`), resolving documentation disparities.
- Automated GPU encoder chain selection supporting `NVENC`, `QSV`, `AMF`, and soft fallbacks.
- Cross-platform system resources detection incorporating `psutil` fallbacks.
- Professional GitHub templates (issues, pull requests) and community health docs.
- Continuous Integration workflow configuration with automated build testing and lint/format checks.
- Comprehensive test suite covering probing fallbacks, encoder capabilities, verifiers, and parallel batch queue processor.

### Fixed
- Fixed typo in logging format (`%param%s` -> `%s`) inside `context_menu.py`.
- Fixed logical check in `is_full_passthrough` in `optimizer.py` that forced invalid `-c copy` commands leading to muxing errors.
- Fixed log path fallback dynamic resolution in `diagnostics.py` when `LOCALAPPDATA` is missing.
- Resolved CLI click commands parameter typing annotations (`input` / `pattern` annotated as `str` instead of `Tuple[str, ...]`).

### Removed
- Removed leftover build executable `context_menu.exe` from repository root.
- Removed dead code functions like `backup_original` in `app.py`.

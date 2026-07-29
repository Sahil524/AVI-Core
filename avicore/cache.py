from __future__ import annotations

import logging
import threading
from pathlib import Path

from avicore.models import MediaInfo
from avicore.probe import probe_media_file

logger = logging.getLogger("avicore.cache")

_PROBE_CACHE: dict[tuple[str, float, int], MediaInfo] = {}
_CACHE_LOCK = threading.Lock()
_MAX_CACHE_ENTRIES = 1000


def probe_media_file_cached(file_path: Path, ffmpeg_path: Path) -> MediaInfo:
    """Probe media file with in-memory caching keyed by path, mtime, and size."""
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = file_path.stat()
    cache_key = (str(file_path), stat.st_mtime, stat.st_size)

    with _CACHE_LOCK:
        if cache_key in _PROBE_CACHE:
            logger.debug(f"Probe cache hit for {file_path.name}")
            return _PROBE_CACHE[cache_key]

    # Probe file
    info = probe_media_file(file_path, ffmpeg_path)

    with _CACHE_LOCK:
        if len(_PROBE_CACHE) >= _MAX_CACHE_ENTRIES:
            # Evict oldest entry
            oldest_key = next(iter(_PROBE_CACHE))
            _PROBE_CACHE.pop(oldest_key, None)

        _PROBE_CACHE[cache_key] = info

    return info


def clear_probe_cache() -> None:
    """Clear all cached probe results."""
    with _CACHE_LOCK:
        _PROBE_CACHE.clear()

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("avicore.capabilities")


def get_config_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = Path(local_app_data) / "AVICore" / "config"
    else:
        base_dir = Path.home() / ".avicore" / "config"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


@dataclass
class HWCapabilities:
    available_encoders: set[str] = field(default_factory=set)
    has_nvenc: bool = False
    has_qsv: bool = False
    has_amf: bool = False
    cpu_cores: int = 4
    gpu_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "available_encoders": list(self.available_encoders),
            "has_nvenc": self.has_nvenc,
            "has_qsv": self.has_qsv,
            "has_amf": self.has_amf,
            "cpu_cores": self.cpu_cores,
            "gpu_names": self.gpu_names,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HWCapabilities:
        return cls(
            available_encoders=set(data.get("available_encoders", [])),
            has_nvenc=data.get("has_nvenc", False),
            has_qsv=data.get("has_qsv", False),
            has_amf=data.get("has_amf", False),
            cpu_cores=data.get("cpu_cores", os.cpu_count() or 4),
            gpu_names=data.get("gpu_names", []),
        )


_CAPABILITIES_CACHE: dict[str, HWCapabilities] = {}
_CAPABILITIES_LOCK = threading.Lock()


def detect_capabilities(ffmpeg_path: Path, force_rebenchmark: bool = False) -> HWCapabilities:
    """Detect available FFmpeg encoders and hardware acceleration capabilities with JSON persistence."""
    key = str(ffmpeg_path.resolve())
    with _CAPABILITIES_LOCK:
        if not force_rebenchmark and key in _CAPABILITIES_CACHE:
            return _CAPABILITIES_CACHE[key]

    config_file = get_config_dir() / "capabilities.json"
    if not force_rebenchmark and config_file.exists():
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
                caps = HWCapabilities.from_dict(data)
                with _CAPABILITIES_LOCK:
                    _CAPABILITIES_CACHE[key] = caps
                return caps
        except Exception as exc:
            logger.warning(f"Failed to load cached capabilities.json: {exc}")

    caps = HWCapabilities(cpu_cores=os.cpu_count() or 4)
    if ffmpeg_path.exists():
        try:
            res = subprocess.run(
                [str(ffmpeg_path), "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and len(parts[0]) == 6 and (parts[0].startswith("V") or parts[0].startswith("A")):
                    encoder_name = parts[1].lower()
                    caps.available_encoders.add(encoder_name)

            caps.has_nvenc = any("nvenc" in enc for enc in caps.available_encoders)
            caps.has_qsv = any("qsv" in enc for enc in caps.available_encoders)
            caps.has_amf = any("amf" in enc for enc in caps.available_encoders)

        except Exception as exc:
            logger.warning(f"Failed to query FFmpeg encoders: {exc}")

    # Save to JSON config file
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(caps.to_dict(), f, indent=2)
    except Exception as exc:
        logger.warning(f"Failed to save capabilities.json: {exc}")

    with _CAPABILITIES_LOCK:
        _CAPABILITIES_CACHE[key] = caps

    return caps

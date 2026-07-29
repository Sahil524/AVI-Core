from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from avicore.capabilities import detect_capabilities, get_config_dir
from avicore.resource_manager import check_system_resources


def collect_system_diagnostics(ffmpeg_path: Path) -> dict[str, Any]:
    """Collect OS, Python, FFmpeg, CPU, and RAM diagnostic details."""
    res_state = check_system_resources()

    ffmpeg_ver = "Unknown"
    if ffmpeg_path.exists():
        try:
            res = subprocess.run(
                [str(ffmpeg_path), "-version"],
                capture_output=True,
                text=True,
            )
            ffmpeg_ver = res.stdout.splitlines()[0] if res.stdout else "Unknown"
        except Exception as exc:
            ffmpeg_ver = f"Error querying version: {exc}"

    caps = detect_capabilities(ffmpeg_path)

    return {
        "timestamp": datetime.now().isoformat(),
        "os": {
            "platform": sys.platform,
            "os_name": os.name,
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "hardware": {
            "cpu_cores": res_state.cpu_cores,
            "total_memory_mb": round(res_state.total_memory_mb, 1),
            "available_memory_mb": round(res_state.available_memory_mb, 1),
            "memory_percent": res_state.memory_percent,
            "has_nvenc": caps.has_nvenc,
            "has_qsv": caps.has_qsv,
            "has_amf": caps.has_amf,
        },
        "ffmpeg": {
            "path": str(ffmpeg_path),
            "version_string": ffmpeg_ver,
            "available_encoders_count": len(caps.available_encoders),
        },
    }


def generate_support_bundle(ffmpeg_path: Path, output_dir: Path) -> Path:
    """Generate a diagnostic ZIP archive containing system info, configs, and logs."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = output_dir / f"avicore_diagnostics_{timestamp}.zip"

    diag_data = collect_system_diagnostics(ffmpeg_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add system info JSON
        zf.writestr("system_info.json", json.dumps(diag_data, indent=2))

        # Add capabilities.json if exists
        cfg_caps = get_config_dir() / "capabilities.json"
        if cfg_caps.exists():
            zf.write(cfg_caps, arcname="capabilities.json")

        # Add log files if exist
        log_file = Path("avicore.log")
        if log_file.exists():
            zf.write(log_file, arcname="avicore.log")

        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            ctx_log = Path(local_appdata) / "AVICore" / "logs" / "avicore_context.log"
        else:
            ctx_log = Path.home() / ".avicore" / "logs" / "avicore_context.log"

        if ctx_log.exists():
            zf.write(ctx_log, arcname="avicore_context.log")

    return zip_path

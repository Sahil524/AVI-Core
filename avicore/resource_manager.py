from __future__ import annotations

import ctypes
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("avicore.resource_manager")


@dataclass
class SystemResourceState:
    memory_percent: float = 0.0
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    cpu_cores: int = 4
    is_throttled: bool = False


def check_system_resources() -> SystemResourceState:
    """Check memory and CPU resources using Win32 API GlobalMemoryStatusEx or psutil fallback."""
    state = SystemResourceState(cpu_cores=os.cpu_count() or 4)

    # Try Win32 API first for zero-dependency Windows execution
    if os.name == "nt":

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        mem = MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            state.memory_percent = float(mem.dwMemoryLoad)
            state.total_memory_mb = mem.ullTotalPhys / (1024 * 1024)
            state.available_memory_mb = mem.ullAvailPhys / (1024 * 1024)
            state.is_throttled = state.memory_percent > 85.0
            return state

    # Fallback to psutil for cross-platform support if installed
    try:
        import psutil

        ps_mem = psutil.virtual_memory()
        state.memory_percent = ps_mem.percent
        state.total_memory_mb = ps_mem.total / (1024 * 1024)
        state.available_memory_mb = ps_mem.available / (1024 * 1024)
        state.is_throttled = state.memory_percent > 85.0
        return state
    except ImportError:
        logger.warning("psutil not available; using default resource monitoring fallback.")

    state.memory_percent = 50.0
    state.available_memory_mb = 4096.0
    return state


def get_optimal_worker_count(is_video: bool = False) -> int:
    """Calculate optimal worker concurrency scaling down if system is under heavy memory pressure."""
    state = check_system_resources()
    if is_video:
        # Video encoding is memory/GPU heavy: max 2 parallel video tasks
        return 1 if state.is_throttled else min(2, state.cpu_cores)
    else:
        # Image processing is CPU bound: scale across cores unless throttled
        return 2 if state.is_throttled else max(1, min(state.cpu_cores, 8))

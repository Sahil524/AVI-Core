from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from typing_extensions import Self

# ============================================================
# Paths and Directories Setup
# ============================================================


def resolve_appdata_paths() -> tuple[Path, Path]:
    """Resolve and create the logs and runtime directories in LOCALAPPDATA."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = Path(local_app_data) / "AVICore"
    else:
        base_dir = Path.home() / ".avicore"

    logs_dir = base_dir / "logs"
    runtime_dir = base_dir / "runtime"

    logs_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    return logs_dir, runtime_dir


LOGS_DIR, RUNTIME_DIR = resolve_appdata_paths()
LOG_FILE_PATH = LOGS_DIR / "avicore_context.log"

# Configure logging at module level
logging.basicConfig(
    filename=str(LOG_FILE_PATH),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    filemode="a",
    force=True,
)
logger = logging.getLogger("avicore.context_menu")


def safe_stderr_write(message: str) -> None:
    """Safely write message to sys.stderr if sys.stderr is not None (windowed/noconsole app compatibility)."""
    if sys.stderr is not None:
        try:
            sys.stderr.write(message + "\n")
        except Exception:
            pass


def get_spool_file_path() -> Path:
    """Resolve the path for the temporary multi-select spool file."""
    temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", os.path.expanduser("~"))))
    return temp_dir / "avicore_spool.txt"


# ============================================================
# File Type and Format Specifications
# ============================================================

IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp"}
VIDEO_FORMATS = {"mp4", "mkv", "mov", "avi", "webm", "m4v", "flv", "ts"}
AUDIO_FORMATS = {"mp3", "wav", "aac", "flac", "ogg", "m4a"}

# ============================================================
# Win32 Named Mutex and Ctypes Configuration
# ============================================================

if sys.platform == "win32":
    # Configure precise Win32 API signatures to prevent 64-bit handle truncation
    ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
    ctypes.windll.kernel32.CreateMutexW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_wchar_p,
    ]

    ctypes.windll.kernel32.WaitForSingleObject.restype = ctypes.c_uint32
    ctypes.windll.kernel32.WaitForSingleObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]

    ctypes.windll.kernel32.ReleaseMutex.restype = ctypes.c_int
    ctypes.windll.kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]

    ctypes.windll.kernel32.CloseHandle.restype = ctypes.c_int
    ctypes.windll.kernel32.CloseHandle.argtypes = [ctypes.c_void_p]


class WindowsNamedMutex:
    """A context manager to handle a Windows Named Mutex with custom blocking behaviors."""

    def __init__(self, name: str, blocking: bool = True):
        self.name = name
        self.blocking = blocking
        self.handle = None
        self.acquired = False

    def __enter__(self) -> Self:
        if sys.platform == "win32":
            self.handle = ctypes.windll.kernel32.CreateMutexW(None, False, self.name)
            if not self.handle:
                local_name = self.name.replace("Global\\", "Local\\")
                self.handle = ctypes.windll.kernel32.CreateMutexW(None, False, local_name)

            if self.handle:
                # 0xFFFFFFFF represents INFINITE blocking, 0 represents non-blocking polling
                timeout = 0xFFFFFFFF if self.blocking else 0
                result = ctypes.windll.kernel32.WaitForSingleObject(self.handle, timeout)
                # 0x00000000 is WAIT_OBJECT_0, 0x00000080 is WAIT_ABANDONED
                if result == 0x00000000 or result == 0x00000080:
                    self.acquired = True
                else:
                    self.acquired = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if sys.platform == "win32" and self.handle:
            if self.acquired:
                ctypes.windll.kernel32.ReleaseMutex(self.handle)
            ctypes.windll.kernel32.CloseHandle(self.handle)


# ============================================================
# Core Functions
# ============================================================


def detect_file_type(file_path: Path) -> str:
    """Detect the category of the file (image, video, or audio) based on extension.

    Returns 'image', 'video', 'audio', or 'unknown'.
    """
    ext = file_path.suffix.lower().lstrip(".")
    if ext in IMAGE_FORMATS:
        return "image"
    elif ext in VIDEO_FORMATS:
        return "video"
    elif ext in AUDIO_FORMATS:
        return "audio"
    return "unknown"


def determine_target_format(file_path: Path, action: str, param: str) -> str | None:
    """Determine or validate the target format for conversion.

    Returns target format (lowercase, no dot) if valid, or None if skipped/invalid.
    """
    if action not in {"convert", "fast-convert"}:
        return None

    target_format = param.lower().strip().lstrip(".")
    if not target_format:
        return None

    file_type = detect_file_type(file_path)

    # Validate target format matches the file type
    if file_type == "image":
        if target_format in IMAGE_FORMATS:
            return target_format
    elif file_type == "video":
        if target_format in VIDEO_FORMATS:
            return target_format
    elif file_type == "audio" and target_format in AUDIO_FORMATS:
        return target_format

    return None


def validate_action(file_path: Path, action: str, param: str) -> bool:
    """Validate if the requested action and parameter are supported for the specific file."""
    if action not in {
        "convert",
        "fast-convert",
        "compress",
        "mute",
        "extract-audio",
        "open",
    }:
        return False

    file_type = detect_file_type(file_path)

    if action == "convert":
        target_format = param.lower().strip().lstrip(".")
        if file_type == "image":
            return target_format in IMAGE_FORMATS
        elif file_type == "video":
            return target_format in VIDEO_FORMATS
        elif file_type == "audio":
            return target_format in AUDIO_FORMATS

    elif action == "fast-convert":
        target_format = param.lower().strip().lstrip(".")
        if file_type == "video":
            return target_format in VIDEO_FORMATS

    elif action == "compress":
        return file_type == "image"

    elif action == "mute" or action == "extract-audio":
        return file_type == "video"

    elif action == "open":
        return file_type in {"image", "video", "audio"}

    return False


def build_command(avicore_path: Path, file_path: Path, action: str, param: str) -> list[str] | None:
    """Build the command list to execute avicore.exe.

    Returns the command elements as a list of strings, or None if the action is skipped.
    """
    if action == "convert":
        target_format = determine_target_format(file_path, action, param)
        if target_format is None:
            return None

        file_type = detect_file_type(file_path)
        if file_type == "image":
            return [
                str(avicore_path),
                "image",
                "convert",
                str(file_path),
                target_format,
            ]
        elif file_type == "video":
            return [
                str(avicore_path),
                "video",
                "convert",
                str(file_path),
                target_format,
            ]
        elif file_type == "audio":
            return [
                str(avicore_path),
                "audio",
                "convert",
                str(file_path),
                target_format,
            ]

    elif action == "fast-convert":
        target_format = determine_target_format(file_path, action, param)
        if target_format is None:
            return None

        file_type = detect_file_type(file_path)
        if file_type == "video":
            return [
                str(avicore_path),
                "video",
                "convert",
                str(file_path),
                target_format,
                "--fast",
            ]

    elif action == "compress":
        return [str(avicore_path), "image", "compress", str(file_path)]

    elif action == "mute":
        return [str(avicore_path), "video", "mute", str(file_path), "--force"]

    elif action == "extract-audio":
        return [str(avicore_path), "audio", "extract", str(file_path)]

    elif action == "open":
        return ["cmd.exe", "/k", f'"{avicore_path}" help']

    return None


def execute_command(cmd: list[str], file_path: Path, action: str) -> subprocess.CompletedProcess[str]:
    """Execute the avicore command with CWD and timeout protection of 7200 seconds."""
    creationflags = 0
    if sys.platform == "win32" and action != "open":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    if action == "open":
        # Launch the cmd.exe window asynchronously so Explorer context menu returns immediately
        subprocess.Popen(cmd, cwd=str(file_path.parent))
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=creationflags,
            cwd=str(RUNTIME_DIR),
            timeout=7200,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_val = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr_val = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "Timeout")

        logger.error(
            "Action: %s | File: %s | Command: %s | Result: FAILURE | Details: Process timed out after 7200 seconds. Out: %s, Err: %s",  # noqa: E501
            action,
            file_path.name,
            " ".join(cmd),
            stdout_val,
            stderr_val,
        )
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=1,
            stdout=stdout_val,
            stderr=stderr_val,
        )


def process_batch(avicore_path: Path, file_paths: list[Path], action: str, param: str) -> tuple[int, int]:
    """Process a list of files sequentially, recording performance and results to the log file."""
    start_batch_time = time.time()
    success_count = 0
    failure_count = 0

    logger.info("--------------------------------------------------------------------------------")
    logger.info(
        "BATCH START | Action: %s | Param: %s | Target Files Count: %d",
        action,
        param,
        len(file_paths),
    )
    logger.info("--------------------------------------------------------------------------------")

    for idx, file_path in enumerate(file_paths, start=1):
        file_start_time = time.time()

        if not file_path.exists():
            logger.warning(
                "[%d/%d] Skipping file (does not exist): %s",
                idx,
                len(file_paths),
                str(file_path),
            )
            failure_count += 1
            continue

        cmd = build_command(avicore_path, file_path, action, param)
        if cmd is None:
            logger.info(
                "[%d/%d] Skipping file (unsupported action or same target format): %s",
                idx,
                len(file_paths),
                file_path.name,
            )
            continue

        result = execute_command(cmd, file_path, action)
        elapsed_sec = time.time() - file_start_time

        if result.returncode == 0:
            success_count += 1
            logger.info(
                "[%d/%d] SUCCESS | File: %s | Time: %.2fs | Cmd: %s",
                idx,
                len(file_paths),
                file_path.name,
                elapsed_sec,
                " ".join(cmd),
            )
        else:
            failure_count += 1
            logger.error(
                "[%d/%d] FAILURE | File: %s | Time: %.2fs | ExitCode: %d | Cmd: %s | Stdout: %s | Stderr: %s",
                idx,
                len(file_paths),
                file_path.name,
                elapsed_sec,
                result.returncode,
                " ".join(cmd),
                result.stdout.strip() if result.stdout else "",
                result.stderr.strip() if result.stderr else "",
            )

    total_batch_time = time.time() - start_batch_time
    logger.info("--------------------------------------------------------------------------------")
    logger.info(
        "BATCH END   | Total Time: %.2fs | Success: %d | Failure: %d",
        total_batch_time,
        success_count,
        failure_count,
    )
    logger.info("--------------------------------------------------------------------------------\n")

    return success_count, failure_count


def find_avicore() -> Path:
    """Locate the avicore executable dynamically."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).parent

    candidates = [
        exe_dir / "avicore.exe",
        exe_dir / "avicore" / "avicore.exe",
        Path(r"C:\Program Files\AVI Core\avicore\avicore.exe"),
        Path(r"C:\Program Files\AVI Core\avicore.exe"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.absolute()

    return Path("avicore.exe")


def show_error_dialog(title: str, message: str) -> None:
    """Show a Windows MessageBox dialog with the error."""
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 | 0x0)  # MB_ICONERROR | MB_OK


def show_info_dialog(title: str, message: str) -> None:
    """Show a Windows MessageBox dialog with information."""
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x0)  # MB_ICONINFORMATION | MB_OK


def refresh_explorer_shell() -> None:
    """Notify Windows shell that file associations have changed."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
        except Exception:
            pass


def is_admin() -> bool:
    """Check if the current process has Windows Administrator privileges."""
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def delete_key_recursive(key, subkey: str) -> bool:
    """Recursively delete a registry key on Windows without handle leaks or uncaught permission crashes."""
    if sys.platform != "win32":
        return False
    import winreg

    try:
        hkey = winreg.OpenKey(key, subkey, 0, winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS)
    except FileNotFoundError:
        return True
    except PermissionError as err:
        logger.error("Permission denied opening registry key for deletion: %s - %s", subkey, err)
        return False
    except OSError as err:
        logger.error("OS error opening registry key for deletion: %s - %s", subkey, err)
        return False

    subkeys = []
    try:
        info = winreg.QueryInfoKey(hkey)
        for i in range(info[0]):
            subkeys.append(winreg.EnumKey(hkey, i))
    except OSError as err:
        logger.error("Error enumerating subkeys under %s: %s", subkey, err)
    finally:
        winreg.CloseKey(hkey)

    success = True
    for sk in subkeys:
        child_path = f"{subkey}\\{sk}"
        if not delete_key_recursive(key, child_path):
            success = False

    try:
        winreg.DeleteKey(key, subkey)
    except FileNotFoundError:
        pass
    except PermissionError as err:
        logger.error("Permission denied deleting registry key: %s - %s", subkey, err)
        return False
    except OSError as err:
        logger.error("OS error deleting registry key: %s - %s", subkey, err)
        return False

    return success


def register_menu_keys(register: bool = True) -> bool:
    """Register or unregister context menu registry entries.

    Uses per-extension SystemFileAssociations\\.ext approach so the menu appears
    regardless of which application owns the file type association.
    """
    if sys.platform != "win32":
        safe_stderr_write("Registry configuration is only supported on Windows.")
        return False

    import winreg

    # Select hive: HKLM if Administrator, otherwise HKCU for user installation
    if is_admin():
        root_key = winreg.HKEY_LOCAL_MACHINE
        base_prefix = r"SOFTWARE\Classes"
    else:
        root_key = winreg.HKEY_CURRENT_USER
        base_prefix = r"Software\Classes"

    logger.info(
        "Starting registry menu %s (Admin: %s, Root Hive: %s)",
        "registration" if register else "unregistration",
        is_admin(),
        "HKLM" if root_key == winreg.HKEY_LOCAL_MACHINE else "HKCU",
    )

    # --- All registry bases to clean ---
    old_global_bases = [
        rf"{base_prefix}\SystemFileAssociations\image\shell\AVICore",
        rf"{base_prefix}\SystemFileAssociations\video\shell\AVICore",
        rf"{base_prefix}\SystemFileAssociations\audio\shell\AVICore",
    ]
    per_ext_bases = [
        rf"{base_prefix}\SystemFileAssociations\.{ext}\shell\AVICore"
        for ext in IMAGE_FORMATS | VIDEO_FORMATS | AUDIO_FORMATS
    ]

    clean_failed = False
    for base in old_global_bases + per_ext_bases:
        if not delete_key_recursive(root_key, base):
            clean_failed = True

    if clean_failed and not is_admin():
        logger.warning("Partial registry cleanup failure. Re-run as Administrator for full HKLM cleanup if needed.")

    if not register:
        message = "AVI Core context menu unregistered successfully!"
        logger.info(message)
        if sys.stdout is not None:
            try:
                print(message)
            except Exception:
                pass
        show_info_dialog("AVI Core Context Menu", message)
        refresh_explorer_shell()
        return True

    try:
        if getattr(sys, "frozen", False):
            exe_path = Path(sys.executable).absolute()
        else:
            exe_path = Path(__file__).absolute()

        logo_path = exe_path.parent / "logo.ico"
        if not logo_path.exists():
            fallback = Path(r"C:\Program Files\AVI Core\logo.ico")
            if fallback.exists():
                logo_path = fallback
            else:
                logger.warning("logo.ico not found at expected path: %s", str(logo_path))

        def set_val(subkey: str, value_name: str, value_data: str) -> None:
            hkey = winreg.CreateKeyEx(root_key, subkey, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.SetValueEx(hkey, value_name, 0, winreg.REG_SZ, value_data)
            finally:
                winreg.CloseKey(hkey)

        def register_image_ext(ext: str) -> None:
            """Register AVI Core submenu for a single image extension."""
            base = rf"{base_prefix}\SystemFileAssociations\.{ext}\shell\AVICore"
            set_val(base, "MUIVerb", "AVI Core")
            set_val(base, "SubCommands", "")
            set_val(base, "MultiSelectModel", "Player")
            set_val(base, "Icon", f'"{logo_path}"')

            # Convert submenu — excludes source extension
            cv = f"{base}\\shell\\1_Convert"
            set_val(cv, "MUIVerb", "Convert")
            set_val(cv, "SubCommands", "")
            set_val(cv, "MultiSelectModel", "Player")
            set_val(cv, "Icon", f'"{logo_path}"')
            for fmt in sorted(IMAGE_FORMATS - {ext}):
                fk = f"{cv}\\shell\\{fmt.upper()}"
                set_val(fk, "MUIVerb", f"Convert To {fmt.upper()}")
                set_val(fk, "MultiSelectModel", "Player")
                set_val(f"{fk}\\command", "", f'"{exe_path}" "convert" "{fmt}" "%1"')

            # Compress Image
            ck = f"{base}\\shell\\2_Compress"
            set_val(ck, "MUIVerb", "Compress Image")
            set_val(ck, "MultiSelectModel", "Player")
            set_val(ck, "Icon", f'"{logo_path}"')
            set_val(f"{ck}\\command", "", f'"{exe_path}" "compress" "none" "%1"')

        def register_video_ext(ext: str) -> None:
            """Register AVI Core submenu for a single video extension."""
            base = rf"{base_prefix}\SystemFileAssociations\.{ext}\shell\AVICore"
            set_val(base, "MUIVerb", "AVI Core")
            set_val(base, "SubCommands", "")
            set_val(base, "MultiSelectModel", "Player")
            set_val(base, "Icon", f'"{logo_path}"')

            # Convert submenu — excludes source extension
            cv = f"{base}\\shell\\1_Convert"
            set_val(cv, "MUIVerb", "Convert")
            set_val(cv, "SubCommands", "")
            set_val(cv, "MultiSelectModel", "Player")
            set_val(cv, "Icon", f'"{logo_path}"')
            for fmt in sorted(VIDEO_FORMATS - {ext}):
                fk = f"{cv}\\shell\\{fmt.upper()}"
                set_val(fk, "MUIVerb", f"Convert To {fmt.upper()}")
                set_val(fk, "MultiSelectModel", "Player")
                set_val(f"{fk}\\command", "", f'"{exe_path}" "fast-convert" "{fmt}" "%1"')

            # Fast Convert submenu — excludes source extension
            fc = f"{base}\\shell\\2_FastConvert"
            set_val(fc, "MUIVerb", "Fast Convert")
            set_val(fc, "SubCommands", "")
            set_val(fc, "MultiSelectModel", "Player")
            set_val(fc, "Icon", f'"{logo_path}"')
            for fmt in sorted(VIDEO_FORMATS - {ext}):
                fk = f"{fc}\\shell\\{fmt.upper()}"
                set_val(fk, "MUIVerb", f"Fast Convert To {fmt.upper()}")
                set_val(fk, "MultiSelectModel", "Player")
                set_val(f"{fk}\\command", "", f'"{exe_path}" "fast-convert" "{fmt}" "%1"')

            # Remove Audio
            mk = f"{base}\\shell\\3_RemoveAudio"
            set_val(mk, "MUIVerb", "Remove Audio")
            set_val(mk, "MultiSelectModel", "Player")
            set_val(mk, "Icon", f'"{logo_path}"')
            set_val(f"{mk}\\command", "", f'"{exe_path}" "mute" "none" "%1"')

            # Extract MP3
            ek = f"{base}\\shell\\4_ExtractMP3"
            set_val(ek, "MUIVerb", "Extract MP3")
            set_val(ek, "MultiSelectModel", "Player")
            set_val(ek, "Icon", f'"{logo_path}"')
            set_val(f"{ek}\\command", "", f'"{exe_path}" "extract-audio" "none" "%1"')

        def register_audio_ext(ext: str) -> None:
            """Register AVI Core submenu for a single audio extension."""
            base = rf"{base_prefix}\SystemFileAssociations\.{ext}\shell\AVICore"
            set_val(base, "MUIVerb", "AVI Core")
            set_val(base, "SubCommands", "")
            set_val(base, "MultiSelectModel", "Player")
            set_val(base, "Icon", f'"{logo_path}"')

            # Convert submenu — excludes source extension
            cv = f"{base}\\shell\\1_Convert"
            set_val(cv, "MUIVerb", "Convert")
            set_val(cv, "SubCommands", "")
            set_val(cv, "MultiSelectModel", "Player")
            set_val(cv, "Icon", f'"{logo_path}"')
            for fmt in sorted(AUDIO_FORMATS - {ext}):
                fk = f"{cv}\\shell\\{fmt.upper()}"
                set_val(fk, "MUIVerb", f"Convert To {fmt.upper()}")
                set_val(fk, "MultiSelectModel", "Player")
                set_val(f"{fk}\\command", "", f'"{exe_path}" "convert" "{fmt}" "%1"')

        # --- Set PerceivedType as a baseline ---
        for ext in IMAGE_FORMATS:
            set_val(rf"{base_prefix}\.{ext}", "PerceivedType", "image")
        for ext in VIDEO_FORMATS:
            set_val(rf"{base_prefix}\.{ext}", "PerceivedType", "video")
        for ext in AUDIO_FORMATS:
            set_val(rf"{base_prefix}\.{ext}", "PerceivedType", "audio")

        # --- Register per-extension context menus ---
        for ext in IMAGE_FORMATS:
            register_image_ext(ext)
        for ext in VIDEO_FORMATS:
            register_video_ext(ext)
        for ext in AUDIO_FORMATS:
            register_audio_ext(ext)

        message = "AVI Core context menu registered successfully!"
        logger.info(message)
        if sys.stdout is not None:
            try:
                print(message)
            except Exception:
                pass
        show_info_dialog("AVI Core Context Menu", message)
        refresh_explorer_shell()
        return True

    except PermissionError as exc:
        message = "Error: Registry write failure. Permission denied.\nPlease run this command as Administrator (Elevated Command Prompt)."  # noqa: E501
        logger.exception("Permission denied during registry key creation: %s", exc)
        safe_stderr_write(message)
        show_error_dialog("AVI Core Registration Error", message)
        return False
    except Exception as exc:
        message = f"Error: Unexpected registry write failure: {exc}"
        logger.exception("Unexpected exception during registry key creation: %s", exc)
        safe_stderr_write(message)
        show_error_dialog("AVI Core Registration Error", message)
        return False


def main() -> None:
    """Main entry point.

    Expects command line arguments:
        context_menu.exe <action> <param> <file_path_1> [file_path_2] ...
        context_menu.exe register
        context_menu.exe unregister
    """
    if len(sys.argv) == 2 and sys.argv[1] in {"register", "unregister"}:
        success = register_menu_keys(sys.argv[1] == "register")
        sys.exit(0 if success else 1)

    if len(sys.argv) < 4:
        safe_stderr_write(
            "Insufficient arguments. Usage: context_menu.exe <action> <param> <file_path_1> [file_path_2] ..."
        )
        sys.exit(1)

    action = sys.argv[1]
    param = sys.argv[2]
    raw_paths = sys.argv[3:]

    if action not in {
        "convert",
        "fast-convert",
        "compress",
        "mute",
        "extract-audio",
        "open",
    }:
        safe_stderr_write(f"Unsupported action: {action}")
        sys.exit(1)

    file_paths: list[Path] = []
    for p in raw_paths:
        try:
            file_paths.append(Path(p).absolute())
        except Exception:
            pass

    if not file_paths:
        safe_stderr_write("No valid file paths resolved.")
        sys.exit(1)

    avicore_path = find_avicore()

    processing_mutex_name = "Global\\AvicoreProcessingMutex"
    spool_mutex_name = "Global\\AvicoreSpoolMutex"

    # --------------------------------------------------------
    # Case A: Multi-file selection passed via CLI directly
    # --------------------------------------------------------
    if len(file_paths) > 1:
        with WindowsNamedMutex(processing_mutex_name, blocking=True) as lock:
            if not lock.acquired:
                sys.exit(1)
            _success_count, failure_count = process_batch(avicore_path, file_paths, action, param)
            sys.exit(0 if failure_count == 0 else 1)

    # --------------------------------------------------------
    # Case B: Single-file call (Explorer multi-select spawns one per file)
    # --------------------------------------------------------
    single_path = file_paths[0]
    spool_file = get_spool_file_path()

    # Try non-blocking acquisition of the processing mutex to detect if Master
    with WindowsNamedMutex(processing_mutex_name, blocking=False) as lock:
        if lock.acquired:
            # We are the MASTER process
            with (
                WindowsNamedMutex(spool_mutex_name, blocking=True),
                open(spool_file, "w", encoding="utf-8") as f,
            ):
                f.write(str(single_path) + "\n")

            time.sleep(0.5)

            accumulated_paths: list[Path] = []
            with WindowsNamedMutex(spool_mutex_name, blocking=True):
                if spool_file.exists():
                    with open(spool_file, encoding="utf-8") as f:
                        for line in f:
                            cleaned = line.strip()
                            if cleaned:
                                accumulated_paths.append(Path(cleaned))
                    try:
                        spool_file.unlink()
                    except OSError:
                        pass

            if not accumulated_paths:
                accumulated_paths = [single_path]

            _success_count, failure_count = process_batch(avicore_path, accumulated_paths, action, param)
            sys.exit(0 if failure_count == 0 else 1)
        else:
            # We are a WORKER process
            with (
                WindowsNamedMutex(spool_mutex_name, blocking=True),
                open(spool_file, "a", encoding="utf-8") as f,
            ):
                f.write(str(single_path) + "\n")
            sys.exit(0)


if __name__ == "__main__":
    main()

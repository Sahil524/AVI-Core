# AVI Core Developer & Contributor Guide

This guide describes how to set up a development environment, run tests, lint the codebase, compile standalone executables, and package installers for **AVI Core**.

---

## 1. Prerequisites

* **Operating System:** Windows 10 or 11 (64-bit) recommended for full context menu and PyInstaller testing. (Linux/macOS supported for core CLI and pipeline development).
* **Python:** Python 3.9 or higher (Python 3.10+ recommended).
* **Git:** Installed and configured.
* **FFmpeg Binary:** A working static `ffmpeg.exe` binary placed in the `bin/` directory or available in system `PATH`.
* **Inno Setup 6 (Optional):** Required only if compiling the Windows setup wizard executable (`AVI-Core-Setup-v2.0.0.exe`).

---

## 2. Setting Up the Environment

### 2.1 Clone the Repository
```powershell
git clone https://github.com/Sahil524/AVI-Core.git
cd "AVI Core"
```

### 2.2 Create a Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate on Linux/macOS
source .venv/bin/activate
```

### 2.3 Install Dependencies
```powershell
# Install runtime dependencies (Click, psutil)
pip install -r requirements.txt

# Install development & test dependencies (pytest, pytest-cov, ruff, mypy, Pillow)
pip install -r requirements-dev.txt
```

---

## 3. Running Locally

### 3.1 Run the CLI in Development
When running from source, execute `app.py` directly:
```powershell
# Check CLI version and options
python app.py --version
python app.py --help

# Test a video stream copy conversion
python app.py video convert sample.mkv mp4 --fast

# Test image conversion
python app.py image convert photo.png webp

# Dry-run mode (prints the FFmpeg command without executing)
python app.py --dry-run video convert sample.mov mp4
```

### 3.2 Test Context Menu Registration Locally
```powershell
# Register context menu from source (points to current app.py / context_menu.py)
python context_menu.py register --silent

# Unregister context menu
python context_menu.py unregister --silent
```

### 3.3 Test Web Frontend Locally
The documentation and Web Converter pages are static HTML/JS files that can be previewed using Python's built-in HTTP server:
```powershell
python -m http.server 8000
```
Navigate to:
* Homepage: `http://localhost:8000/index.html`
* Web Converter: `http://localhost:8000/converter.html`
* CLI Docs: `http://localhost:8000/cli.html`

---

## 4. Running Tests & Quality Verification

AVI Core uses `pytest` for unit and integration testing.

### 4.1 Run the Test Suite
```powershell
pytest tests/ -v
```

### 4.2 Run Test Coverage
```powershell
pytest tests/ --cov=avicore --cov-report=term-missing
```

### 4.3 Static Linting with Ruff
Configuration is managed in `pyproject.toml`:
```powershell
# Check for lint errors
ruff check .

# Check formatting
ruff format --check .
```

### 4.4 Static Type Checking with Mypy
```powershell
mypy avicore app.py
```

---

## 5. Building Standalone Binaries

AVI Core uses PyInstaller via the automated build script `build_binaries.ps1`:

```powershell
powershell -ExecutionPolicy Bypass -File build_binaries.ps1
```

### What the Build Script Does:
1. **Verification:** Validates Python version, confirms `bin/ffmpeg.exe` exists, and inspects `logo.ico` with Pillow to ensure all standard Windows icon sizes (16x16, 32x32, 48x48, 256x256) are present.
2. **Build `avicore.exe`:** Compiles `app.py` in `--onedir` mode with `ffmpeg.exe` bundled directly alongside the executable.
3. **Build `context_menu.exe`:** Compiles `context_menu.py` in `--onefile --noconsole` mode so Explorer actions execute silently without a console window.
4. **Output Verification:** Verifies compiled binaries exist in `dist/` and extracts binary icon resources using Win32 API to ensure Windows Explorer can display the AVI Core logo icon.

---

## 6. Building the Inno Setup Installer

To compile the graphical setup wizard:

1. Ensure `dist/avicore` and `dist/context_menu.exe` have been built using Step 5.
2. Install [Inno Setup 6](https://jrsoftware.org/isdl.php) if not already installed.
3. Compile `installer.iss`:
   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```
4. The output installer `AVI-Core-Setup-v2.0.0.exe` will be generated in `dist/`.

---

## 7. Development Architecture Notes

When contributing new features or modifying pipelines, adhere to these architectural rules:

1. **Non-Destructive Storage:** Never overwrite a source file directly without verifying the output first. Always write to a temporary file (`_tmp`), run verification (`verify_output_file`), vault the original to `./backup/`, and atomically rename.
2. **Signal Cleanliness:** Register any temporary files created during processing in `CREATED_FILES` so `SIGINT` (Ctrl+C) handlers can clean them up if the user interrupts execution.
3. **Graceful Fallbacks:** When implementing hardware acceleration, always provide a CPU fallback (e.g. `libx264`) if hardware encoders (NVENC/QSV/AMF) are unavailable.
4. **No External Telemetry:** AVI Core is strictly local-first and offline. Do not introduce network calls, analytics, or remote tracking.

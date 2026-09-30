# AVI Core Installation & Deployment Guide

This guide details the requirements, installation methods, verification steps, upgrade procedures, and troubleshooting for **AVI Core** (version 2.0.0) on Windows.

---

## 1. System Requirements

* **Operating System:** Windows 10 (64-bit) or Windows 11 (64-bit).
* **Architecture:** x86_64 / AMD64.
* **Disk Space:** ~150 MB for the core binaries, bundled FFmpeg executable, and iconography.
* **Administrative Privileges:** Optional. AVI Core can be installed at user scope (`HKCU`) without administrator permissions or at machine scope (`HKLM`) with elevation.
* **Dependencies:** None. The standalone distribution packages Python, Click, psutil, and static FFmpeg into self-contained executables.

---

## 2. Installation Options

AVI Core offers two primary installation methods:

```text
┌────────────────────────────────────────────────────────┐
│                   Choose an Option                     │
├────────────────────────────┬───────────────────────────┤
│ Option A: Setup Wizard     │ Option B: PowerShell      │
│ (Inno Setup Executable)    │ (Automated Script)        │
│ • Best for standard users  │ • Best for developers     │
│ • Full graphical wizard    │ • Scriptable & silent     │
│ • Automatic Start Menu     │ • User or Machine scope   │
└────────────────────────────┴───────────────────────────┘
```

---

### Option A: Inno Setup Wizard (`AVI-Core-Setup-v2.0.0.exe`)

This is the recommended method for end users.

1. Download `AVI-Core-Setup-v2.0.0.exe` from the [GitHub Releases](https://github.com/Sahil524/AVI-Core/releases).
2. Double-click the downloaded executable.
3. If prompted by Windows SmartScreen, select **More info** -> **Run anyway**.
4. Follow the setup wizard prompts:
   * **Destination Directory:** Defaults to `C:\Program Files\AVI Core` (when elevated) or `%LOCALAPPDATA%\Programs\AVICore`.
   * **Components:** Installs `avicore.exe`, `context_menu.exe`, `ffmpeg.exe`, and `logo.ico`.
5. The installer will automatically:
   * Append the `avicore` directory to the system or user `PATH` environment variable.
   * Register the Windows Explorer right-click cascading context menus.
   * Create Start Menu shortcuts for AVI Core and the uninstaller.
6. Click **Finish**.

---

### Option B: PowerShell Automated Installer (`install.ps1` / `install.bat`)

This method is suitable for automated deployments, headless machines, and developers working directly from the repository.

#### Quick Install via Batch Wrapper
Double-click `install.bat` from File Explorer, or open Command Prompt:
```cmd
install.bat
```
The batch wrapper launches PowerShell with `-ExecutionPolicy Bypass -NoProfile` to avoid Windows script execution policy restrictions.

#### Advanced PowerShell Execution
Open PowerShell and run:
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 [OPTIONS]
```

#### Available Parameters:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `-Scope` | `User` \| `Machine` \| `Auto` | `Auto` | `User` installs to `%LOCALAPPDATA%\Programs\AVICore` without admin rights. `Machine` installs to `C:\Program Files\AVI Core` (requires elevation). `Auto` checks administrator privileges automatically. |
| `-InstallDir` | String | Auto-resolved | Custom target installation directory path. |
| `-NoPrompt` | Switch | False | Disables the "Press Enter to exit" prompt when run non-interactively in automated pipelines. |
| `-BuildIfMissing`| Switch | False | Invokes `build_binaries.ps1` to compile binaries from source if `dist/` is not present. |

#### What the PowerShell Installer Does:
1. **Safety Shutdown:** Detects if `avicore.exe` or `context_menu.exe` is currently running and terminates them cleanly to avoid file locks.
2. **File Deployment:** Copies `dist/avicore/*`, `dist/context_menu.exe`, and `logo.ico` to the target directory.
3. **Environment Configuration:** Permanently updates the user or machine `PATH` environment variable.
4. **Context Menu Registration:** Invokes `context_menu.exe register --silent` to set up all 19 supported file extensions.
5. **Logging:** Appends all installation steps and any warnings to `%LOCALAPPDATA%\AVICore\logs\installer.log`.

---

## 3. Verifying the Installation

### 3.1 Verify the CLI
Open a new Command Prompt or PowerShell window (to load the updated `PATH`) and run:
```powershell
avicore --version
```
Expected output:
```text
avicore v2.0.0
```

Run the built-in diagnostic help command:
```powershell
avicore --help
```

### 3.2 Verify the Windows Explorer Context Menu
1. Open Windows File Explorer.
2. Navigate to any supported file (e.g., a `.mp4`, `.mkv`, or `.png` file).
3. Right-click the file.
4. Locate the **AVI Core** menu item (featuring the gold AVI Core icon):
   * On Windows 10: Appears directly in the main context menu.
   * On Windows 11: Appears under **Show more options** (or directly on the main menu if classic context menus are enabled).
5. Hover over **Convert** or **Fast Convert** to verify the submenus populate with target formats.

---

## 4. Upgrading & Reinstallation

When upgrading from an older version of AVI Core:

1. You do not need to manually uninstall the previous version. Both the Inno Setup installer and `install.ps1` detect existing installations.
2. The installer will check the global application mutex (`Global\AvicoreProcessingMutex`) and stop any running instances before overwriting files.
3. Obsolete registry keys from older versions are recursively deleted and replaced with current keys.
4. System and user `PATH` entries are refreshed to prevent duplicate entries.

---

## 5. Uninstallation

### Via Windows Settings
1. Open Windows **Settings** (`Win + I`) -> **Apps** -> **Installed apps**.
2. Search for **AVI Core**.
3. Click the three dots (`...`) and select **Uninstall**.

### Via Uninstall Script
Run `uninstall.bat` or execute PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File uninstall.ps1
```
The uninstall script:
* Terminates any active AVI Core processes.
* Unregisters all context menu registry entries under `HKCU` and `HKLM`.
* Removes the installation directory from the user or system `PATH`.
* Deletes installed binary files.
* Asks whether to preserve or purge diagnostic logs in `%LOCALAPPDATA%\AVICore\logs`.

### Via CLI Command
To remove context menus without uninstalling the CLI tool:
```powershell
avicore menu remove
```

---

## 6. Troubleshooting & Common Issues

### Issue 1: PowerShell script closes immediately when launched
* **Cause:** When double-clicking `.ps1` files in File Explorer, Windows executes them via PowerShell ConsoleHost which exits immediately upon completion or on error.
* **Resolution:** Use `install.bat`, or open PowerShell manually and run:
  ```powershell
  powershell -ExecutionPolicy Bypass -File install.ps1
  ```

### Issue 2: "Execution of scripts is disabled on this system"
* **Cause:** Windows default PowerShell execution policy (`Restricted`).
* **Resolution:** Use the `-ExecutionPolicy Bypass` flag when calling the script:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install.ps1
  ```

### Issue 3: Context menu does not appear after installation
* **Cause:** Windows File Explorer caches shell extension associations in memory.
* **Resolution:**
  1. Restart Windows Explorer:
     ```powershell
     Stop-Process -Name explorer -Force
     ```
  2. Verify that `context_menu.exe` was registered:
     ```powershell
     avicore menu install
     ```
  3. On Windows 11, check inside **Show more options** (`Shift + F10`).

### Issue 4: Antivirus / Windows Defender False Positive
* **Cause:** Standalone executables generated with PyInstaller can occasionally trigger heuristics in third-party antivirus software.
* **Resolution:** AVI Core is 100% open source under the MIT license. You can inspect the source code, verify that zero telemetry exists, and compile the binaries directly on your machine using `build_binaries.ps1`.

### 5. Log File Locations
If an installation or context menu operation fails, check the log files:
* **Installer Log:** `%LOCALAPPDATA%\AVICore\logs\installer.log`
* **Context Menu Log:** `%LOCALAPPDATA%\AVICore\logs\avicore_context.log`
* **CLI Log:** `avicore.log` (in the current working directory when run with `--verbose`)

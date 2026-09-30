# Contributing to AVI Core

Thank you for your interest in contributing to **AVI Core**! We welcome bug reports, feature suggestions, documentation enhancements, and code contributions.

---

## 1. Ground Rules & Principles

* **100% Offline & Private:** AVI Core is strictly local-first. Under no circumstances should features introduce external network telemetry, analytics, or remote tracking.
* **Non-Destructive Storage:** Operations must never destroy or corrupt user master files. Always follow the established safety lifecycle: write to temporary staging buffers (`_tmp`), verify output integrity, vault raw sources to `./backup/`, and atomically commit.
* **Performance Conscious:** Context menu and CLI tools should run efficiently without high memory usage, process thrashing, or blocking Windows Explorer.

---

## 2. Reporting Bugs

Before reporting a bug, check existing [GitHub Issues](https://github.com/Sahil524/AVI-Core/issues) to avoid duplicates.

### Generating a Diagnostic Bundle:
If you encounter an issue on your machine, run the built-in diagnostic command:
```powershell
avicore system diagnostics
```
This generates a ZIP file (e.g. `avicore_diagnostics_<timestamp>.zip`) containing:
* FFmpeg version and hardware encoder detection output.
* Operating system release and architecture.
* Recent lines from `avicore.log` and `%LOCALAPPDATA%\AVICore\logs\avicore_context.log`.

### What to Include in a Bug Report:
1. **Description:** A clear summary of what happened vs what you expected to happen.
2. **Steps to Reproduce:** The exact CLI command used or the sequence of actions in File Explorer.
3. **Media Details:** File container, source codecs, and file size (e.g., "4K H.264 video in MKV container converting to MP4").
4. **Environment:** Windows 10 or 11 version (e.g., Windows 11 23H2), GPU model if applicable.
5. **Logs / Diagnostics:** Attach the diagnostic ZIP or relevant log snippets.

---

## 3. Suggesting Features

If you have an idea for a new feature or improvement:
1. Open a [GitHub Issue](https://github.com/Sahil524/AVI-Core/issues) titled `[Feature Request]: <Short description>`.
2. Explain the use case and why it benefits Windows users.
3. Consider whether the feature aligns with AVI Core's local-first, privacy-focused mission.

---

## 4. Development Workflow

### 4.1 Fork and Clone
```powershell
git clone https://github.com/<your-username>/AVI-Core.git
cd "AVI Core"
```

### 4.2 Set Up Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

### 4.3 Create a Feature Branch
```powershell
git checkout -b feature/my-new-feature
```

### 4.4 Run Tests & Quality Checks
Before submitting your changes, verify that the test suite and linters pass:

```powershell
# Run unit and integration tests
pytest tests/ -v

# Run test coverage check
pytest tests/ --cov=avicore

# Run Ruff linter and formatter checks
ruff check .
ruff format --check .

# Run static type checks
mypy avicore app.py
```

### 4.5 Submitting a Pull Request
1. Push your branch to your fork:
   ```powershell
   git push origin feature/my-new-feature
   ```
2. Open a Pull Request against the `main` branch of `Sahil524/AVI-Core`.
3. Provide a clear PR description explaining what was changed, why, and how you tested it.
4. Ensure all continuous integration checks pass.

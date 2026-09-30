# Security Policy for AVI Core

The AVI Core development team takes security and user privacy seriously. This document outlines supported versions, vulnerability reporting procedures, and key security design considerations.

---

## 1. Supported Versions

Security updates and patches are actively provided for the following releases:

| Version | Supported | Status |
| :--- | :--- | :--- |
| **2.0.x** | ✅ Yes | Current active production release. |
| **< 2.0.0** | ❌ No | Deprecated. Users are encouraged to upgrade to v2.0.0+. |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability or sensitive flaw in AVI Core:

1. **Do NOT open a public GitHub issue** with reproducible exploit instructions or payloads.
2. Submit your report privately using [GitHub Security Advisories](https://github.com/Sahil524/AVI-Core/security/advisories/new).
3. If GitHub Advisories are not accessible, open an issue requesting a private security coordination channel without disclosing vulnerability specifics in the issue text.

### What to Include in a Report:
* Description of the vulnerability and its potential impact.
* Specific affected component (CLI, Windows context menu, registry handler, pipeline engine, or web converter).
* Minimal proof-of-concept steps or test media demonstrating the issue.
* Any proposed mitigations or patch suggestions if available.

### Response Timeline:
* We aim to acknowledge vulnerability reports within **48 hours**.
* If confirmed, a fix will be developed and released in an expedited patch release alongside appropriate attribution.

---

## 3. Security Architecture & Threat Model

AVI Core's architecture is designed around defensive principles:

### 3.1 Local-First & Zero Network Transmission
* AVI Core performs all media conversions directly on the local host machine using bundled static FFmpeg binaries or client-side browser engines.
* The application makes **zero network connections**, transmits zero telemetry, and performs no background updates or telemetry pings.

### 3.2 Safe Subprocess Invocation
* FFmpeg commands are constructed deterministically as structured argument arrays (`list[str]`) passed directly to `subprocess.run()`.
* At no point does AVI Core execute arbitrary command strings via shell interpreters (`shell=True`), preventing command-injection attacks through maliciously crafted file names.

### 3.3 Path Traversal & File Safety
* All file paths passed from CLI or Windows Explorer are resolved and normalized using Python's `pathlib.Path`.
* The two-phase atomic commit model prevents accidental truncation of master media files if processing is aborted or power is lost.
* Master source files are automatically copied to an isolated `./backup/` directory prior to destination replacement.

### 3.4 Windows Registry Privileges
* When executed by non-administrative users, context menu registrations are written exclusively to `HKEY_CURRENT_USER\Software\Classes`.
* Administrative elevation is never requested unless the user explicitly opts into machine-wide installation under `HKEY_LOCAL_MACHINE`.

# Train Simulator Classic - .RWP Installer & Mod Manager

[![Release](https://img.shields.io/github/v/release/Madhav-Gajjar/TSC-rwp-Installer?color=89b4fa&style=flat-square)](https://github.com/Madhav-Gajjar/TSC-rwp-Installer/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://github.com/Madhav-Gajjar/TSC-rwp-Installer)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

A dedicated, high-speed Windows installer and mod manager for **Train Simulator Classic** (RailWorks). It simplifies installing `.rwp` addon packages, handles automatic extraction of nested `.ap` archives, and provides full mod tracking with one-click uninstallation.

---

## Prerequisites

### For Standard Use (Standalone Executable)

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Game Installation**: An active installation of Train Simulator Classic (RailWorks) via Steam or standalone.
- **7-Zip (Recommended)**: While the application includes an internal extraction engine, having [7-Zip](https://www.7-zip.org/) installed (`7z.exe`) is recommended for significantly faster decompression of multi-gigabyte route files and `.ap` archives. The application automatically detects default 7-Zip installation paths.
- **File Permissions**: Write permissions to your `railworks` root directory (especially if located in `C:\Program Files (x86)\Steam`).

### For Development & Running from Source

- **Python**: Version 3.10 or newer.
- **Tkinter**: Standard Windows Python installations include Tkinter (`tcl/tk`) by default.
- **PyInstaller** *(Optional)*: Required only if building the standalone binary from source.

---

## Key Features

- **Queue-Based .RWP Installation**:
  - Automatically parses `.rwp` archives and maps `Assets`, `Content/Routes`, and `Manuals` into their correct target directories.
  - Supports queuing individual files or scanning entire folders of `.rwp` packages.

- **Automatic .AP Archive Extraction**:
  - Detects compressed `.ap` archives (e.g., `MainContent.ap`, `*Assets.ap`) within routes and asset trees and unpacks them in-place.
  - Eliminates the need for manual archive navigation when installing community reskins, sound improvements, and enhancement packs.

- **Mod Installation Tracking & Rollback**:
  - Tracks all installed modifications, timestamps, file manifests, and disk footprints in a persistent local registry (`tsc_installed_mods.json`).
  - **Manifest Viewer**: Inspect the exact list of files installed by any registered package.
  - **Clean Uninstallation**: Removes installed files and prunes orphaned empty directories without modifying core game files.

- **Pre-Extracted Folder Support**:
  - Ingest pre-extracted folders containing `Assets/` or `Content/` structures directly into the game directory.

- **Dual Decompression Engine**:
  - Leverages local 7-Zip installations for accelerated extraction with graceful fallback to Python's internal extraction libraries.

- **Batch .AP Unpacker Utility**:
  - Built-in utility to scan the entire RailWorks directory and extract all remaining packed `.ap` archives in a single batch operation.

---

## Installation and Usage

### Using the Standalone Application

1. Download the latest `TSC_RWP_Installer.exe` from the [Releases](https://github.com/Madhav-Gajjar/TSC-rwp-Installer/releases) page.
2. Launch `TSC_RWP_Installer.exe`.
3. Verify your RailWorks directory:
   - The application automatically attempts to detect your Steam installation path.
   - If not found automatically, click **Browse...** to specify your `railworks` directory (for example, `D:\SteamLibrary\steamapps\common\railworks`).
4. Add addon packages to the installation queue:
   - **Add .rwp Files...**: Select one or more `.rwp` files.
   - **Add Folder of .rwp...**: Queue all packages found in a directory.
   - **Add Extracted Folder...**: Process loose folders already organized into `Assets` or `Content`.
5. Click **Install Queued Addons**.

---

## Development Setup

### Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/Madhav-Gajjar/TSC-rwp-Installer.git
   cd TSC-rwp-Installer
   ```

2. Run the application:
   ```bash
   python main.py
   ```

### Building the Executable

To compile into a standalone `.exe`:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="TSC_RWP_Installer" main.py
```

The resulting executable will be placed in the `dist/` directory.

---

## License

This project is distributed under the terms of the [MIT License](LICENSE).

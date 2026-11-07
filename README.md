# Train Simulator Classic - .RWP Installer & Mod Manager

A dedicated, high-speed Windows installer and mod manager for **Train Simulator Classic** (RailWorks).

---

## 🌟 Key Features

1. **One-Click .RWP Installation**:
   - Automatically parses `.rwp` packages and installs `Assets`, `Content/Routes`, and `Manuals` into their proper game locations.
2. **Automatic .AP Archive Unpacking**:
   - Automatically detects compressed `.ap` archives (e.g. `MainContent.ap`, `*Assets.ap`) inside routes and asset folders and unpacks them in-place.
   - Saves hours of manual 7-Zip extraction when installing reskins, sound mods, and enhancements!
3. **Mod Installation History & Rollback**:
   - Records every installed mod, installation date, file count, and total size in `tsc_installed_mods.json`.
   - **File Manifest Viewer**: View the exact list of files installed by any mod.
   - **One-Click Uninstall**: Cleanly remove all files installed by a mod and prune empty folders without touching other game files.
4. **Pre-Extracted Folder Support**:
   - If you already extracted `.rwp` files into `Assets/`, `Content/`, and `Manuals/`, you can use **"📂 Add Extracted Folder..."** to sync and unpack them into your game folder.
5. **7-Zip Acceleration & Fallback**:
   - Automatically detects 7-Zip for lightning-fast multi-gigabyte route extractions.
   - Includes a built-in ZIP engine if 7-Zip is not installed.
6. **Batch .AP Unpacker Tool**:
   - A dedicated utility tool to scan your existing RailWorks directory for packed `.ap` archives and unpack them all at once.

---

## 🚀 How to Run

1. Double-click **`TSC_RWP_Installer.exe`**.
2. **Game Directory**:
   - The installer will attempt to auto-detect your RailWorks installation folder.
   - Or click **"Browse..."** and choose your game directory (e.g. `D:\SteamLibrary\steamapps\common\railworks`).
3. **Add Addons**:
   - Click **"➕ Add .rwp Files..."** to pick `.rwp` archives.
   - Click **"📁 Add Folder of .rwp..."** to queue all `.rwp` files in a folder.
   - Or click **"📂 Add Extracted Folder..."** if you have pre-extracted folders.
4. Click **"🚀 Install Queued Addons"**.
5. Once completed, your addon will be ready to play in Train Simulator Classic, and the source `.rwp` file will be moved to the `Installed/` folder!


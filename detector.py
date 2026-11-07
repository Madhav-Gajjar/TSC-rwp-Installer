import os
import re
import winreg

def is_valid_game_dir(path):
    if not path or not os.path.isdir(path):
        return False
    # Check for RailWorks.exe or RailWorks64.exe
    if os.path.exists(os.path.join(path, "RailWorks.exe")) or os.path.exists(os.path.join(path, "RailWorks64.exe")):
        return True
    # Or check if Assets and Content folders exist
    if os.path.isdir(os.path.join(path, "Assets")) and os.path.isdir(os.path.join(path, "Content")):
        return True
    return False

def get_steam_libraries():
    libraries = []
    steam_path = None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
    except Exception:
        pass

    if not steam_path:
        for p in [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]:
            if os.path.isdir(p):
                steam_path = p
                break

    if steam_path:
        steam_path = os.path.normpath(steam_path)
        libraries.append(steam_path)
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Find all "path" "..."
                matches = re.findall(r'"path"\s+"([^"]+)"', content)
                for m in matches:
                    norm = os.path.normpath(m.replace("\\\\", "\\"))
                    if norm not in libraries and os.path.isdir(norm):
                        libraries.append(norm)
            except Exception:
                pass

    # Check common drives as fallback
    for drive in ["C:", "D:", "E:", "F:", "G:"]:
        for sub in [r"SteamLibrary", r"Games\Steam", r"Steam"]:
            test_path = os.path.join(drive + "\\", sub)
            if os.path.isdir(test_path) and test_path not in libraries:
                libraries.append(test_path)

    return libraries

def detect_train_simulator_path():
    # 1. Check registry specific to RailWorks
    for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for subkey in [
            r"SOFTWARE\WOW6432Node\RailSimulator.com\RailWorks",
            r"SOFTWARE\RailSimulator.com\RailWorks",
            r"SOFTWARE\Valve\Steam\Apps\24010"
        ]:
            try:
                k = winreg.OpenKey(root, subkey)
                val, _ = winreg.QueryValueEx(k, "InstallDir" if "RailSimulator" in subkey else "Installed")
                winreg.CloseKey(k)
                if val and isinstance(val, str) and is_valid_game_dir(val):
                    return os.path.normpath(val)
            except Exception:
                pass

    # 2. Check all Steam libraries
    for lib in get_steam_libraries():
        candidate = os.path.join(lib, "steamapps", "common", "railworks")
        if is_valid_game_dir(candidate):
            return candidate

    return ""


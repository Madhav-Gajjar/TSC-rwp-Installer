import os
import json
import sys

def get_app_dir():
    """Returns the directory where the application/exe is running from."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_app_dir(), "tsc_installer_config.json")
HISTORY_FILE = os.path.join(get_app_dir(), "tsc_installed_mods.json")

DEFAULT_CONFIG = {
    "game_dir": "",
    "extract_ap": True,
    "keep_ap_after_extract": True,
    "move_to_installed": True,
    "overwrite_existing": True,
    "seven_zip_path": "",
    "last_source_dir": ""
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = dict(DEFAULT_CONFIG)
                config.update(data)
                return config
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")


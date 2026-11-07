import os
import json
import time
import uuid
try:
    from .config import HISTORY_FILE
except ImportError:
    from config import HISTORY_FILE

class ModHistoryManager:
    def __init__(self, history_file=None):
        self.history_file = history_file or HISTORY_FILE

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading history: {e}")
        return []

    def save_history(self, records):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_record(self, name, source_file, game_dir, installed_files, extracted_ap_count=0, total_size_bytes=0):
        records = self.load_history()
        mod_id = f"mod_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        entry = {
            "id": mod_id,
            "name": name,
            "source_file": source_file,
            "install_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "game_dir": game_dir,
            "file_count": len(installed_files),
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "extracted_ap_count": extracted_ap_count,
            "status": "Installed",
            "installed_files": installed_files  # relative paths to game_dir
        }
        # Check if mod with same name already in list, if so keep or update
        records.insert(0, entry)
        self.save_history(records)
        return entry

    def get_record(self, mod_id):
        records = self.load_history()
        for r in records:
            if r.get("id") == mod_id:
                return r
        return None

    def uninstall_mod(self, mod_id, callback=None):
        """
        Uninstalls files tracked by mod_id from the game directory.
        callback(step_msg, current, total)
        """
        records = self.load_history()
        target = None
        for r in records:
            if r.get("id") == mod_id:
                target = r
                break

        if not target:
            return False, "Mod record not found."

        game_dir = target.get("game_dir", "")
        if not os.path.isdir(game_dir):
            return False, f"Game directory not accessible: {game_dir}"

        files = target.get("installed_files", [])
        total = len(files)
        deleted_count = 0
        directories_to_check = set()

        for idx, rel_path in enumerate(files):
            full_path = os.path.join(game_dir, rel_path)
            if callback and idx % 20 == 0:
                callback(f"Removing {rel_path}...", idx, total)
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    deleted_count += 1
                    parent = os.path.dirname(full_path)
                    directories_to_check.add(parent)
            except Exception as e:
                print(f"Failed to remove {full_path}: {e}")

        # Clean up empty parent directories
        # Sort directories by depth descending so deepest gets cleaned first
        sorted_dirs = sorted(directories_to_check, key=lambda d: len(d), reverse=True)
        for d in sorted_dirs:
            try:
                # Do not delete root folders like Assets, Content, Manuals
                rel = os.path.relpath(d, game_dir)
                if rel.lower() in [".", "assets", "content", "manuals"]:
                    continue
                if os.path.isdir(d) and not os.listdir(d):
                    os.rmdir(d)
            except Exception:
                pass

        target["status"] = "Uninstalled"
        target["uninstall_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.save_history(records)

        if callback:
            callback(f"Uninstallation complete. {deleted_count} files removed.", total, total)

        return True, f"Successfully removed {deleted_count} files."

    def remove_record(self, mod_id):
        records = self.load_history()
        records = [r for r in records if r.get("id") != mod_id]
        self.save_history(records)

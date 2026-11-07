import os
import shutil
import zipfile
import subprocess
import re
import sys
try:
    from .detector import is_valid_game_dir
    from .history import ModHistoryManager
except ImportError:
    from detector import is_valid_game_dir
    from history import ModHistoryManager

def find_7z_binary(custom_path=None):
    if custom_path and os.path.isfile(custom_path):
        return custom_path
    
    # Check default paths
    candidates = [
        shutil.which("7z"),
        shutil.which("7z.exe"),
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe"
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None

def normalize_archive_path(path):
    return path.replace("\\", "/").lstrip("/")

def get_archive_file_list(archive_path, seven_zip=None):
    """Returns list of relative file paths in the archive."""
    file_list = []
    # Try zipfile first
    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            for item in zf.infolist():
                if not item.is_dir():
                    file_list.append(item.filename.replace("\\", "/"))
            return file_list
    except Exception:
        pass

    # Try 7z if available
    seven_z = find_7z_binary(seven_zip)
    if seven_z:
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            result = subprocess.run(
                [seven_z, "l", "-slt", archive_path],
                capture_output=True,
                text=True,
                errors="ignore",
                startupinfo=startupinfo
            )
            current_path = None
            is_folder = False
            for line in result.stdout.splitlines():
                if line.startswith("Path = "):
                    current_path = line[7:].strip()
                elif line.startswith("Folder = "):
                    is_folder = line[9:].strip() == "+"
                elif line == "" and current_path:
                    if not is_folder and current_path != archive_path:
                        file_list.append(current_path.replace("\\", "/"))
                    current_path = None
                    is_folder = False
            if current_path and not is_folder and current_path != archive_path:
                file_list.append(current_path.replace("\\", "/"))
        except Exception as e:
            print(f"7z list error: {e}")

    return file_list

def extract_with_7z(seven_z, archive_path, dest_dir, progress_cb=None):
    """Extracts archive using 7-Zip with progress callback."""
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    cmd = [seven_z, "x", archive_path, f"-o{dest_dir}", "-y", "-bsp1"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="ignore",
        startupinfo=startupinfo
    )

    percent_regex = re.compile(r"([0-9]+)%")
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line and progress_cb:
            m = percent_regex.search(line)
            if m:
                try:
                    pct = int(m.group(1))
                    progress_cb(f"Extracting with 7-Zip... {pct}%", pct, 100)
                except ValueError:
                    pass

    return proc.returncode == 0

def extract_with_zipfile(archive_path, dest_dir, progress_cb=None):
    """Fallback pure-Python ZIP extraction with progress reporting."""
    with zipfile.ZipFile(archive_path, "r") as zf:
        members = [m for m in zf.infolist() if not m.is_dir()]
        total = len(members)
        for idx, member in enumerate(members):
            target_path = os.path.join(dest_dir, member.filename.replace("/", os.sep))
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zf.open(member) as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)
            if progress_cb and (idx % 25 == 0 or idx == total - 1):
                pct = int((idx + 1) / total * 100)
                progress_cb(f"Extracting: {os.path.basename(member.filename)} ({pct}%)", idx + 1, total)
    return True

def extract_archive(archive_path, dest_dir, seven_zip=None, progress_cb=None):
    os.makedirs(dest_dir, exist_ok=True)
    seven_z = find_7z_binary(seven_zip)
    if seven_z:
        try:
            success = extract_with_7z(seven_z, archive_path, dest_dir, progress_cb)
            if success:
                return True
        except Exception as e:
            if progress_cb:
                progress_cb(f"7-Zip notice: {e}, falling back to built-in extractor", 0, 100)

    # Fallback to python zipfile
    return extract_with_zipfile(archive_path, dest_dir, progress_cb)

def determine_strip_prefix(file_list):
    """
    Checks if archive has a top-level wrapper directory before Assets/Content/Manuals.
    E.g. 'MyRouteMod/Assets/...' -> strip 'MyRouteMod/'
    """
    prefixes = set()
    for f in file_list:
        parts = f.replace("\\", "/").split("/")
        for idx, p in enumerate(parts):
            if p.lower() in ["assets", "content", "manuals"]:
                if idx > 0:
                    prefixes.add("/".join(parts[:idx]) + "/")
                break
    if len(prefixes) == 1:
        return list(prefixes)[0]
    return ""

def install_rwp(rwp_path, game_dir, options=None, seven_zip=None, progress_cb=None, log_cb=None):
    """
    Installs a single .rwp file into game_dir.
    options = {
        'extract_ap': True,
        'keep_ap_after_extract': True,
        'move_to_installed': True,
        'overwrite_existing': True
    }
    """
    if options is None:
        options = {}
    extract_ap = options.get("extract_ap", True)
    keep_ap = options.get("keep_ap_after_extract", True)
    move_to_installed = options.get("move_to_installed", True)

    def log(msg):
        if log_cb:
            log_cb(msg)
        print(msg)

    mod_name = os.path.splitext(os.path.basename(rwp_path))[0]
    # Remove leading numbering like '1012101 = ' if present
    clean_mod_name = re.sub(r"^\d+\s*=\s*", "", mod_name).strip()
    log(f"--- Starting Installation: {clean_mod_name} ---")

    if not os.path.isfile(rwp_path):
        return False, f"File not found: {rwp_path}"

    if not is_valid_game_dir(game_dir):
        return False, f"Invalid Train Simulator game directory: {game_dir}"

    archive_files = get_archive_file_list(rwp_path, seven_zip)
    if not archive_files:
        return False, f"Could not inspect or read archive {os.path.basename(rwp_path)}"

    strip_prefix = determine_strip_prefix(archive_files)
    if strip_prefix:
        log(f"Detected top-level wrapper prefix: '{strip_prefix}'. Will extract directly to game structure.")

    # We extract into game_dir
    log(f"Extracting package '{os.path.basename(rwp_path)}' to game directory...")
    if progress_cb:
        progress_cb(f"Extracting {os.path.basename(rwp_path)}...", 0, 100)

    # If strip_prefix is needed, extract to a temp staging directory, then copy with prefix stripped
    installed_manifest = []
    total_bytes = 0

    if strip_prefix:
        temp_stage = os.path.join(game_dir, "_tsc_stage_temp")
        os.makedirs(temp_stage, exist_ok=True)
        try:
            extract_archive(rwp_path, temp_stage, seven_zip, progress_cb)
            source_root = os.path.join(temp_stage, strip_prefix.replace("/", os.sep))
            for root, dirs, files in os.walk(source_root):
                for f in files:
                    src_file = os.path.join(root, f)
                    rel = os.path.relpath(src_file, source_root)
                    dest_file = os.path.join(game_dir, rel)
                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    installed_manifest.append(rel)
                    total_bytes += os.path.getsize(dest_file)
        finally:
            if os.path.isdir(temp_stage):
                shutil.rmtree(temp_stage, ignore_errors=True)
    else:
        extract_archive(rwp_path, game_dir, seven_zip, progress_cb)
        for rel in archive_files:
            rel_norm = os.path.normpath(rel)
            installed_manifest.append(rel_norm)
            full_p = os.path.join(game_dir, rel_norm)
            if os.path.isfile(full_p):
                total_bytes += os.path.getsize(full_p)

    log(f"Base .rwp extracted: {len(installed_manifest)} files.")

    # Find and unpack any .ap archives if extract_ap is enabled
    ap_extracted_count = 0
    if extract_ap:
        log("Scanning for nested .ap archives to unpack...")
        # Search among files installed from this archive
        ap_candidates = [f for f in installed_manifest if f.lower().endswith(".ap")]
        for ap_rel in ap_candidates:
            ap_full = os.path.join(game_dir, ap_rel)
            if not os.path.isfile(ap_full):
                continue
            ap_dir = os.path.dirname(ap_full)
            ap_name = os.path.basename(ap_full)
            log(f"Unpacking .ap archive: {ap_name} into {os.path.relpath(ap_dir, game_dir)}...")
            if progress_cb:
                progress_cb(f"Unpacking {ap_name}...", 0, 100)

            ap_files = get_archive_file_list(ap_full, seven_zip)
            extract_archive(ap_full, ap_dir, seven_zip, progress_cb)
            ap_extracted_count += 1

            for sub_f in ap_files:
                sub_rel = os.path.relpath(os.path.join(ap_dir, sub_f.replace("/", os.sep)), game_dir)
                installed_manifest.append(sub_rel)
                sub_full = os.path.join(game_dir, sub_rel)
                if os.path.isfile(sub_full):
                    total_bytes += os.path.getsize(sub_full)

            if not keep_ap:
                log(f"Removing original .ap: {ap_name}")
                try:
                    os.remove(ap_full)
                    if ap_rel in installed_manifest:
                        installed_manifest.remove(ap_rel)
                except Exception as e:
                    log(f"Warning: could not delete .ap: {e}")

    # Deduplicate manifest
    installed_manifest = list(dict.fromkeys(installed_manifest))

    # Record to history
    history_mgr = ModHistoryManager()
    history_mgr.add_record(
        name=clean_mod_name,
        source_file=os.path.abspath(rwp_path),
        game_dir=os.path.abspath(game_dir),
        installed_files=installed_manifest,
        extracted_ap_count=ap_extracted_count,
        total_size_bytes=total_bytes
    )
    log(f"Successfully registered '{clean_mod_name}' in mod history database.")

    # Move to Installed folder if option is set
    if move_to_installed:
        source_dir = os.path.dirname(os.path.abspath(rwp_path))
        installed_dir = os.path.join(source_dir, "Installed")
        os.makedirs(installed_dir, exist_ok=True)
        target_path = os.path.join(installed_dir, os.path.basename(rwp_path))
        try:
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                target_path = f"{base}_{int(os.path.getmtime(rwp_path))}{ext}"
            shutil.move(rwp_path, target_path)
            log(f"Moved source .rwp to: {target_path}")
        except Exception as e:
            log(f"Note: Could not move .rwp to Installed folder: {e}")

    log(f"[SUCCESS] Finished installing '{clean_mod_name}'! Total files: {len(installed_manifest)}, AP archives unpacked: {ap_extracted_count}.")
    if progress_cb:
        progress_cb(f"Completed {clean_mod_name}!", 100, 100)

    return True, f"Installed {clean_mod_name} ({len(installed_manifest)} files)"

def install_extracted_folder(source_folder, game_dir, options=None, seven_zip=None, progress_cb=None, log_cb=None):
    """
    Installs from a pre-extracted folder containing Assets, Content, and/or Manuals.
    """
    if options is None:
        options = {}
    extract_ap = options.get("extract_ap", True)
    keep_ap = options.get("keep_ap_after_extract", True)

    def log(msg):
        if log_cb:
            log_cb(msg)
        print(msg)

    folder_name = os.path.basename(os.path.abspath(source_folder))
    log(f"--- Starting Installation from Extracted Folder: {folder_name} ---")

    if not is_valid_game_dir(game_dir):
        return False, f"Invalid Train Simulator game directory: {game_dir}"

    subfolders_to_copy = []
    for sf in ["Assets", "Content", "Manuals"]:
        p = os.path.join(source_folder, sf)
        if os.path.isdir(p):
            subfolders_to_copy.append(sf)

    if not subfolders_to_copy:
        return False, f"No Assets, Content, or Manuals subfolders found in {source_folder}."

    installed_manifest = []
    total_bytes = 0

    # Count files to copy for progress
    all_files_to_copy = []
    for sf in subfolders_to_copy:
        sf_root = os.path.join(source_folder, sf)
        for root, dirs, files in os.walk(sf_root):
            for f in files:
                all_files_to_copy.append(os.path.join(root, f))

    total_files = len(all_files_to_copy)
    log(f"Copying {total_files} files from {', '.join(subfolders_to_copy)} to game directory...")

    for idx, src_path in enumerate(all_files_to_copy):
        rel = os.path.relpath(src_path, source_folder)
        dest_path = os.path.join(game_dir, rel)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        installed_manifest.append(rel)
        total_bytes += os.path.getsize(dest_path)
        if progress_cb and (idx % 20 == 0 or idx == total_files - 1):
            pct = int((idx + 1) / total_files * 100)
            progress_cb(f"Copying files... ({pct}%)", idx + 1, total_files)

    ap_extracted_count = 0
    if extract_ap:
        log("Scanning for nested .ap archives to unpack...")
        ap_candidates = [f for f in installed_manifest if f.lower().endswith(".ap")]
        for ap_rel in ap_candidates:
            ap_full = os.path.join(game_dir, ap_rel)
            if not os.path.isfile(ap_full):
                continue
            ap_dir = os.path.dirname(ap_full)
            ap_name = os.path.basename(ap_full)
            log(f"Unpacking .ap archive: {ap_name} into {os.path.relpath(ap_dir, game_dir)}...")
            if progress_cb:
                progress_cb(f"Unpacking {ap_name}...", 0, 100)

            ap_files = get_archive_file_list(ap_full, seven_zip)
            extract_archive(ap_full, ap_dir, seven_zip, progress_cb)
            ap_extracted_count += 1

            for sub_f in ap_files:
                sub_rel = os.path.relpath(os.path.join(ap_dir, sub_f.replace("/", os.sep)), game_dir)
                installed_manifest.append(sub_rel)
                sub_full = os.path.join(game_dir, sub_rel)
                if os.path.isfile(sub_full):
                    total_bytes += os.path.getsize(sub_full)

            if not keep_ap:
                log(f"Removing original .ap: {ap_name}")
                try:
                    os.remove(ap_full)
                    if ap_rel in installed_manifest:
                        installed_manifest.remove(ap_rel)
                except Exception as e:
                    log(f"Warning: could not delete .ap: {e}")

    installed_manifest = list(dict.fromkeys(installed_manifest))

    history_mgr = ModHistoryManager()
    history_mgr.add_record(
        name=f"Folder: {folder_name}",
        source_file=os.path.abspath(source_folder),
        game_dir=os.path.abspath(game_dir),
        installed_files=installed_manifest,
        extracted_ap_count=ap_extracted_count,
        total_size_bytes=total_bytes
    )

    log(f"[SUCCESS] Extracted folder sync complete! Total files: {len(installed_manifest)}, AP unpacked: {ap_extracted_count}.")
    if progress_cb:
        progress_cb(f"Completed {folder_name}!", 100, 100)

    return True, f"Installed from {folder_name} ({len(installed_manifest)} files)"

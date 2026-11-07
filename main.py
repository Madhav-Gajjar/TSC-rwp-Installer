import sys
import os
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from detector import detect_train_simulator_path, is_valid_game_dir
    from extractor import install_rwp, install_extracted_folder
    from history import ModHistoryManager
    from gui import run_gui
except ImportError:
    from installer_src.detector import detect_train_simulator_path, is_valid_game_dir
    from installer_src.extractor import install_rwp, install_extracted_folder
    from installer_src.history import ModHistoryManager
    from installer_src.gui import run_gui

def main():
    parser = argparse.ArgumentParser(description="Train Simulator Classic - .RWP Installer & Mod Manager")
    parser.add_argument("--game-dir", "-g", help="Path to Train Simulator Classic (railworks) directory")
    parser.add_argument("--rwp", "-r", nargs="+", help="One or more .rwp files to install")
    parser.add_argument("--folder", "-f", help="Folder containing extracted Assets/Content/Manuals to install")
    parser.add_argument("--no-ap", action="store_true", help="Do not extract nested .ap archives")
    parser.add_argument("--delete-ap", action="store_true", help="Delete .ap archives after extracting")
    parser.add_argument("--no-move", action="store_true", help="Do not move .rwp to Installed folder")
    parser.add_argument("--headless", action="store_true", help="Run in CLI headless mode (no GUI)")

    args = parser.parse_args()

    # If any specific command line arguments are provided that indicate batch/CLI usage
    if args.headless or args.rwp or args.folder:
        game_dir = args.game_dir
        if not game_dir:
            game_dir = detect_train_simulator_path()
        if not is_valid_game_dir(game_dir):
            print(f"[ERROR] Invalid or undetected game directory: '{game_dir}'")
            print("Please specify a valid Train Simulator Classic directory with --game-dir.")
            sys.exit(1)

        options = {
            "extract_ap": not args.no_ap,
            "keep_ap_after_extract": not args.delete_ap,
            "move_to_installed": not args.no_move
        }

        if args.rwp:
            for rwp in args.rwp:
                print(f"Installing {rwp}...")
                ok, msg = install_rwp(rwp, game_dir, options=options)
                print(msg)

        if args.folder:
            print(f"Installing from extracted folder {args.folder}...")
            ok, msg = install_extracted_folder(args.folder, game_dir, options=options)
            print(msg)
        return

    # Otherwise, run interactive GUI
    run_gui()

if __name__ == "__main__":
    main()

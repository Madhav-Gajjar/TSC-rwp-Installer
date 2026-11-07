import os
import shutil
import tempfile
import zipfile
import sys

# Ensure installer_src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "installer_src"))
from detector import is_valid_game_dir
from history import ModHistoryManager
from extractor import install_rwp, extract_archive

def run_tests():
    print("Starting tests...")
    temp_dir = tempfile.mkdtemp(prefix="tsc_test_")
    try:
        # 1. Setup mock game directory
        mock_game = os.path.join(temp_dir, "RailWorks")
        os.makedirs(os.path.join(mock_game, "Assets"), exist_ok=True)
        os.makedirs(os.path.join(mock_game, "Content"), exist_ok=True)
        with open(os.path.join(mock_game, "RailWorks.exe"), "w") as f:
            f.write("mock")

        assert is_valid_game_dir(mock_game), "mock game dir should be valid"
        print("✓ Game dir validation passed")

        # 2. Create a mock .ap archive
        mock_ap_path = os.path.join(temp_dir, "TestPack.ap")
        with zipfile.ZipFile(mock_ap_path, "w") as zf:
            zf.writestr("Models/TestLoco.bin", "sample binary content")
            zf.writestr("Textures/TestLoco.TgPcDx", "sample texture content")

        # 3. Create a mock .rwp containing Assets, Content, Manuals and the .ap archive
        mock_rwp_path = os.path.join(temp_dir, "TestAddon.rwp")
        with zipfile.ZipFile(mock_rwp_path, "w") as zf:
            zf.writestr("Manuals/EN/Guide.pdf", "mock manual")
            zf.writestr("Assets/TestDev/TestAddon/readme.txt", "mock readme")
            # Put the .ap inside Assets/TestDev/TestAddon/TestPack.ap
            with open(mock_ap_path, "rb") as ap_in:
                zf.writestr("Assets/TestDev/TestAddon/TestPack.ap", ap_in.read())

        # 4. Test installation with ModHistoryManager
        hist_file = os.path.join(temp_dir, "test_history.json")
        hist_mgr = ModHistoryManager(history_file=hist_file)

        options = {
            "extract_ap": True,
            "keep_ap_after_extract": True,
            "move_to_installed": True,
            "overwrite_existing": True
        }

        # Monkeypatch history file
        import history
        history.HISTORY_FILE = hist_file
        import extractor
        extractor.ModHistoryManager = lambda: hist_mgr

        success, msg = install_rwp(mock_rwp_path, mock_game, options=options)
        assert success, f"Installation failed: {msg}"
        print(f"✓ Installation succeeded: {msg}")

        # Verify extracted files
        assert os.path.isfile(os.path.join(mock_game, "Manuals", "EN", "Guide.pdf")), "Manual not installed"
        assert os.path.isfile(os.path.join(mock_game, "Assets", "TestDev", "TestAddon", "readme.txt")), "Readme not installed"
        assert os.path.isfile(os.path.join(mock_game, "Assets", "TestDev", "TestAddon", "TestPack.ap")), "AP not installed"
        # Verify nested .ap was unpacked in its folder!
        unpacked_bin = os.path.join(mock_game, "Assets", "TestDev", "TestAddon", "Models", "TestLoco.bin")
        assert os.path.isfile(unpacked_bin), f"Nested .ap file was not unpacked to: {unpacked_bin}"
        print("✓ Nested .ap archive unpacked in-place successfully!")

        # Verify history record
        records = hist_mgr.load_history()
        assert len(records) == 1, "Expected 1 history record"
        rec = records[0]
        print(f"✓ History record verified: {rec['name']}, files: {rec['file_count']}, AP unpacked: {rec['extracted_ap_count']}")
        assert rec['extracted_ap_count'] == 1, "Should have 1 AP unpacked"

        # Verify rwp was moved to Installed
        installed_rwp = os.path.join(temp_dir, "Installed", "TestAddon.rwp")
        assert os.path.isfile(installed_rwp), f"RWP not moved to Installed: {installed_rwp}"
        print("✓ RWP moved to Installed folder verified")

        # 5. Test uninstallation
        uninst_ok, uninst_msg = hist_mgr.uninstall_mod(rec["id"])
        assert uninst_ok, f"Uninstallation failed: {uninst_msg}"
        assert not os.path.isfile(unpacked_bin), "Uninstalled file still exists"
        print("✓ Uninstallation verified, files cleanly removed!")

        print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_tests()


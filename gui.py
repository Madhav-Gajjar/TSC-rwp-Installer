import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
try:
    from .config import load_config, save_config, get_app_dir
    from .detector import detect_train_simulator_path, is_valid_game_dir
    from .extractor import install_rwp, install_extracted_folder, find_7z_binary, extract_archive, get_archive_file_list
    from .history import ModHistoryManager
except ImportError:
    from config import load_config, save_config, get_app_dir
    from detector import detect_train_simulator_path, is_valid_game_dir
    from extractor import install_rwp, install_extracted_folder, find_7z_binary, extract_archive, get_archive_file_list
    from history import ModHistoryManager

class ModernRWPInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Train Simulator Classic - .RWP Installer & Mod Manager")
        self.root.geometry("980x720")
        self.root.minsize(850, 600)

        self.config = load_config()
        self.history_mgr = ModHistoryManager()
        self.queue = []  # list of dicts: {'path': ..., 'name': ..., 'size': ..., 'status': ..., 'type': 'rwp'|'folder'}
        self.is_working = False

        self._setup_styles()
        self._build_ui()
        self._init_defaults()

    def _setup_styles(self):
        self.bg_color = "#181825"
        self.card_bg = "#1e1e2e"
        self.border_color = "#313244"
        self.accent_color = "#89b4fa"
        self.text_color = "#cdd6f4"
        self.text_muted = "#a6adc8"
        self.success_color = "#a6e3a1"
        self.danger_color = "#f38ba8"

        self.root.configure(bg=self.bg_color)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 9))
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground=self.text_color, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#45475a")], foreground=[("selected", self.accent_color)])

        style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        style.configure("TLabel", background=self.card_bg, foreground=self.text_color)
        style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"), foreground=self.accent_color)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground=self.text_muted)

        style.configure("TCheckbutton", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", self.card_bg)])

        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#3b82f6", foreground="#ffffff", padding=[14, 6])
        style.map("Accent.TButton", background=[("active", "#2563eb"), ("disabled", "#4b5563")])

        style.configure("Secondary.TButton", font=("Segoe UI", 9), background="#313244", foreground=self.text_color, padding=[10, 5])
        style.map("Secondary.TButton", background=[("active", "#45475a")])

        style.configure("Treeview", 
                        background="#11111b", 
                        foreground=self.text_color, 
                        fieldbackground="#11111b", 
                        rowheight=26, 
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", 
                        background="#313244", 
                        foreground="#cdd6f4", 
                        font=("Segoe UI", 9, "bold"), 
                        relief="flat")
        style.map("Treeview", background=[("selected", "#45475a")], foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", "#45475a")])

        style.configure("TProgressbar", thickness=14, troughcolor="#11111b", background="#89b4fa")

    def _build_ui(self):
        # Header banner
        header_frame = tk.Frame(self.root, bg="#11111b", height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(header_frame, text="🚂 Train Simulator Classic - Addon Installer & Mod Manager", 
                             font=("Segoe UI", 14, "bold"), bg="#11111b", fg="#89b4fa")
        title_lbl.pack(side=tk.LEFT, padx=20, pady=12)

        self.seven_z_badge = tk.Label(header_frame, text="", font=("Segoe UI", 8), bg="#313244", fg="#a6e3a1", padx=8, pady=3)
        self.seven_z_badge.pack(side=tk.RIGHT, padx=20, pady=15)

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self.install_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.history_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.tools_tab = tk.Frame(self.notebook, bg=self.bg_color)

        self.notebook.add(self.install_tab, text="  📦 Addon Installer  ")
        self.notebook.add(self.history_tab, text="  📜 Installation History  ")
        self.notebook.add(self.tools_tab, text="  ⚙ Tools & Unpack Utilities  ")

        self._build_installer_tab()
        self._build_history_tab()
        self._build_tools_tab()

    def _build_installer_tab(self):
        # Card 1: Game Directory
        game_frame = ttk.Frame(self.install_tab, style="Card.TFrame", padding=12)
        game_frame.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(game_frame, text="Train Simulator Classic Game Directory:", style="Header.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 6))

        self.game_dir_var = tk.StringVar()
        self.game_entry = tk.Entry(game_frame, textvariable=self.game_dir_var, bg="#11111b", fg=self.text_color, 
                                   insertbackground=self.text_color, font=("Segoe UI", 9), relief="flat", highlightthickness=1, highlightcolor=self.accent_color)
        self.game_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=4)
        game_frame.columnconfigure(0, weight=1)

        btn_browse = ttk.Button(game_frame, text="Browse...", style="Secondary.TButton", command=self._browse_game_dir)
        btn_browse.grid(row=1, column=1, padx=(0, 6))

        btn_detect = ttk.Button(game_frame, text="Auto-Detect", style="Secondary.TButton", command=self._auto_detect_game_dir)
        btn_detect.grid(row=1, column=2)

        self.game_status_lbl = tk.Label(game_frame, text="", bg=self.card_bg, font=("Segoe UI", 8))
        self.game_status_lbl.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(4, 0))
        self.game_dir_var.trace_add("write", lambda *args: self._validate_game_dir())

        # Card 2: Queue / Files to install
        queue_frame = ttk.Frame(self.install_tab, style="Card.TFrame", padding=12)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Toolbar
        tb = tk.Frame(queue_frame, bg=self.card_bg)
        tb.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(tb, text="Addons to Install:", style="Header.TLabel").pack(side=tk.LEFT)

        btn_clear = ttk.Button(tb, text="Clear List", style="Secondary.TButton", command=self._clear_queue)
        btn_clear.pack(side=tk.RIGHT, padx=(4, 0))

        btn_add_ext = ttk.Button(tb, text="📂 Add Extracted Folder...", style="Secondary.TButton", command=self._add_extracted_folder)
        btn_add_ext.pack(side=tk.RIGHT, padx=4)

        btn_add_dir = ttk.Button(tb, text="📁 Add Folder of .rwp...", style="Secondary.TButton", command=self._add_folder_rwp)
        btn_add_dir.pack(side=tk.RIGHT, padx=4)

        btn_add_files = ttk.Button(tb, text="➕ Add .rwp Files...", style="Accent.TButton", command=self._add_rwp_files)
        btn_add_files.pack(side=tk.RIGHT, padx=4)

        # Queue Treeview
        tree_container = tk.Frame(queue_frame, bg="#11111b")
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("Name", "Size", "Type", "Status", "Path")
        self.queue_tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="extended")
        self.queue_tree.heading("Name", text="Addon Name")
        self.queue_tree.heading("Size", text="Size")
        self.queue_tree.heading("Type", text="Package Type")
        self.queue_tree.heading("Status", text="Status")
        self.queue_tree.heading("Path", text="Source Path")

        self.queue_tree.column("Name", width=340)
        self.queue_tree.column("Size", width=90, anchor=tk.E)
        self.queue_tree.column("Type", width=110, anchor=tk.CENTER)
        self.queue_tree.column("Status", width=120, anchor=tk.CENTER)
        self.queue_tree.column("Path", width=260)

        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=tree_scroll.set)

        self.queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Card 3: Options & Action
        opts_frame = ttk.Frame(self.install_tab, style="Card.TFrame", padding=10)
        opts_frame.pack(fill=tk.X, padx=8, pady=4)

        self.opt_extract_ap = tk.BooleanVar(value=self.config.get("extract_ap", True))
        self.opt_keep_ap = tk.BooleanVar(value=self.config.get("keep_ap_after_extract", True))
        self.opt_move_installed = tk.BooleanVar(value=self.config.get("move_to_installed", True))

        cb_ap = ttk.Checkbutton(opts_frame, text="⚡ Extract & unpack nested .ap archives (Models, textures, routes)", variable=self.opt_extract_ap, command=self._save_options)
        cb_ap.grid(row=0, column=0, sticky=tk.W, padx=8, pady=2)

        cb_keep = ttk.Checkbutton(opts_frame, text="Keep original .ap archives alongside unpacked files", variable=self.opt_keep_ap, command=self._save_options)
        cb_keep.grid(row=0, column=1, sticky=tk.W, padx=8, pady=2)

        cb_move = ttk.Checkbutton(opts_frame, text="Move installed .rwp to 'Installed' subfolder", variable=self.opt_move_installed, command=self._save_options)
        cb_move.grid(row=0, column=2, sticky=tk.W, padx=8, pady=2)

        # Install Execution Section
        act_frame = tk.Frame(self.install_tab, bg=self.bg_color)
        act_frame.pack(fill=tk.X, padx=8, pady=6)

        self.btn_install = ttk.Button(act_frame, text="🚀 Install Queued Addons", style="Accent.TButton", command=self._start_installation)
        self.btn_install.pack(side=tk.RIGHT, padx=6)

        self.progress_bar = ttk.Progressbar(act_frame, style="TProgressbar", mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.status_detail_lbl = tk.Label(self.install_tab, text="Ready", bg=self.bg_color, fg=self.text_muted, font=("Segoe UI", 9))
        self.status_detail_lbl.pack(anchor=tk.W, padx=12, pady=(0, 2))

        # Collapsible log
        log_frame = ttk.Frame(self.install_tab, style="Card.TFrame", padding=6)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=8, pady=(0, 6))

        self.log_text = tk.Text(log_frame, height=5, bg="#11111b", fg="#a6adc8", font=("Consolas", 8), relief="flat", wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _build_history_tab(self):
        hist_frame = ttk.Frame(self.history_tab, style="Card.TFrame", padding=12)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Top toolbar
        h_tb = tk.Frame(hist_frame, bg=self.card_bg)
        h_tb.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(h_tb, text="Mod Installation History:", style="Header.TLabel").pack(side=tk.LEFT)

        btn_open_game = ttk.Button(h_tb, text="📂 Open Game Folder", style="Secondary.TButton", command=self._open_game_folder)
        btn_open_game.pack(side=tk.RIGHT, padx=4)

        btn_refresh = ttk.Button(h_tb, text="🔄 Refresh", style="Secondary.TButton", command=self._refresh_history)
        btn_refresh.pack(side=tk.RIGHT, padx=4)

        # Search box
        search_lbl = tk.Label(h_tb, text="Search:", bg=self.card_bg, fg=self.text_muted, font=("Segoe UI", 9))
        search_lbl.pack(side=tk.RIGHT, padx=(12, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_history())
        search_entry = tk.Entry(h_tb, textvariable=self.search_var, bg="#11111b", fg=self.text_color, insertbackground=self.text_color, font=("Segoe UI", 9), width=18, relief="flat")
        search_entry.pack(side=tk.RIGHT, ipady=3)

        # History Treeview
        tree_container = tk.Frame(hist_frame, bg="#11111b")
        tree_container.pack(fill=tk.BOTH, expand=True)

        cols = ("Name", "Install Date", "Files", "AP Unpacked", "Size (MB)", "Status", "ID")
        self.hist_tree = ttk.Treeview(tree_container, columns=cols, show="headings", selectmode="browse")
        self.hist_tree.heading("Name", text="Mod Name")
        self.hist_tree.heading("Install Date", text="Installed On")
        self.hist_tree.heading("Files", text="Files Tracked")
        self.hist_tree.heading("AP Unpacked", text="AP Archives")
        self.hist_tree.heading("Size (MB)", text="Size (MB)")
        self.hist_tree.heading("Status", text="Status")
        self.hist_tree.heading("ID", text="Record ID")

        self.hist_tree.column("Name", width=300)
        self.hist_tree.column("Install Date", width=150, anchor=tk.CENTER)
        self.hist_tree.column("Files", width=95, anchor=tk.E)
        self.hist_tree.column("AP Unpacked", width=95, anchor=tk.CENTER)
        self.hist_tree.column("Size (MB)", width=90, anchor=tk.E)
        self.hist_tree.column("Status", width=95, anchor=tk.CENTER)
        self.hist_tree.column("ID", width=120)

        hist_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=hist_scroll.set)

        self.hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Action bar at bottom
        h_action_bar = tk.Frame(hist_frame, bg=self.card_bg)
        h_action_bar.pack(fill=tk.X, pady=(10, 0))

        btn_manifest = ttk.Button(h_action_bar, text="📄 View Installed Files Manifest...", style="Secondary.TButton", command=self._view_manifest)
        btn_manifest.pack(side=tk.LEFT, padx=(0, 6))

        btn_uninstall = ttk.Button(h_action_bar, text="❌ Uninstall Selected Mod...", style="Secondary.TButton", command=self._uninstall_selected_mod)
        btn_uninstall.pack(side=tk.LEFT, padx=6)

        btn_del_rec = ttk.Button(h_action_bar, text="🗑 Delete Record Only", style="Secondary.TButton", command=self._delete_record_only)
        btn_del_rec.pack(side=tk.RIGHT, padx=4)

    def _build_tools_tab(self):
        tools_frame = ttk.Frame(self.tools_tab, style="Card.TFrame", padding=16)
        tools_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Section 1: 7-Zip Setup
        ttk.Label(tools_frame, text="7-Zip Acceleration Engine", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 4))
        desc_7z = ("7-Zip provides 5x-10x faster extraction for multi-gigabyte .rwp and .ap route packages.\n"
                   "The installer automatically discovers 7-Zip on your system or uses the built-in extractor fallback.")
        ttk.Label(tools_frame, text=desc_7z, style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        f_7z = tk.Frame(tools_frame, bg=self.card_bg)
        f_7z.pack(fill=tk.X, pady=(0, 16))

        self.seven_z_path_var = tk.StringVar(value=self.config.get("seven_zip_path", ""))
        self.entry_7z = tk.Entry(f_7z, textvariable=self.seven_z_path_var, bg="#11111b", fg=self.text_color, font=("Segoe UI", 9), relief="flat")
        self.entry_7z.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)

        btn_browse_7z = ttk.Button(f_7z, text="Browse 7z.exe...", style="Secondary.TButton", command=self._browse_7z)
        btn_browse_7z.pack(side=tk.LEFT, padx=4)

        btn_test_7z = ttk.Button(f_7z, text="Detect & Test", style="Secondary.TButton", command=self._check_7z_status)
        btn_test_7z.pack(side=tk.LEFT, padx=4)

        ttk.Separator(tools_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)

        # Section 2: Batch AP Extractor
        ttk.Label(tools_frame, text="Batch .AP Archive Unpacker for Game Directory", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 4))
        desc_ap = ("Scan your entire Train Simulator Assets and Routes folders for packed .ap archives and unpack them in-place.\n"
                   "This is essential for installing third-party reskins, sound mods, and route enhancements.")
        ttk.Label(tools_frame, text=desc_ap, style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 10))

        btn_scan_ap = ttk.Button(tools_frame, text="🔍 Scan & Unpack All .AP Archives in Game Directory...", style="Accent.TButton", command=self._batch_unpack_ap)
        btn_scan_ap.pack(anchor=tk.W, pady=6)

    def _init_defaults(self):
        # 1. Game directory
        saved_game = self.config.get("game_dir", "")
        if saved_game and is_valid_game_dir(saved_game):
            self.game_dir_var.set(saved_game)
        else:
            detected = detect_train_simulator_path()
            if detected:
                self.game_dir_var.set(detected)
        self._validate_game_dir()

        # 2. 7-Zip
        self._check_7z_status()

        # 3. Load history
        self._refresh_history()

        # 4. Check if current directory has .rwp files or extracted folders, and auto-populate
        app_dir = get_app_dir()
        self._auto_scan_source_folder(app_dir)

    def _auto_scan_source_folder(self, folder):
        if not os.path.isdir(folder):
            return
        # Find .rwp files in folder
        rwp_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".rwp")]
        for rwp in rwp_files:
            self._add_queue_item(rwp, "rwp")

        # Check if folder itself has Assets/Content/Manuals
        has_extracted = any(os.path.isdir(os.path.join(folder, sf)) for sf in ["Assets", "Content", "Manuals"])
        if has_extracted:
            # Check if there are .ap files inside
            self._add_queue_item(folder, "folder")

    def _check_7z_status(self):
        custom = self.seven_z_path_var.get().strip()
        binary = find_7z_binary(custom if custom else None)
        if binary:
            self.seven_z_badge.config(text=f"✓ 7-Zip Accelerated: {os.path.basename(binary)}", fg="#a6e3a1")
            self.log("7-Zip detected and active: " + binary)
        else:
            self.seven_z_badge.config(text="⚠ Built-in ZIP Engine (7-Zip not detected)", fg="#f9e2af")
            self.log("Note: 7-Zip not detected. Built-in ZIP extractor will be used.")

    def _browse_7z(self):
        f = filedialog.askopenfilename(title="Select 7z.exe", filetypes=[("7-Zip Executable", "7z.exe"), ("All Files", "*.*")])
        if f:
            self.seven_z_path_var.set(f)
            self.config["seven_zip_path"] = f
            save_config(self.config)
            self._check_7z_status()

    def _validate_game_dir(self):
        path = self.game_dir_var.get().strip()
        if not path:
            self.game_status_lbl.config(text="⚠ Please select or auto-detect your Train Simulator Classic directory.", fg="#f9e2af")
            return False
        if is_valid_game_dir(path):
            self.game_status_lbl.config(text="✓ Valid Train Simulator Classic directory detected.", fg="#a6e3a1")
            self.config["game_dir"] = path
            save_config(self.config)
            return True
        else:
            self.game_status_lbl.config(text="⚠ Warning: Selected directory does not appear to contain RailWorks.exe or Assets/Content folders.", fg="#f38ba8")
            return False

    def _browse_game_dir(self):
        dir_selected = filedialog.askdirectory(title="Select Train Simulator Classic Installation Directory (railworks)")
        if dir_selected:
            self.game_dir_var.set(os.path.normpath(dir_selected))

    def _auto_detect_game_dir(self):
        detected = detect_train_simulator_path()
        if detected:
            self.game_dir_var.set(detected)
            messagebox.showinfo("Train Simulator Classic Found", f"Auto-detected RailWorks directory:\n{detected}")
        else:
            messagebox.showwarning("Not Found", "Could not automatically locate RailWorks.\nPlease browse to your game folder manually (e.g. Steam/steamapps/common/railworks).")

    def _save_options(self):
        self.config["extract_ap"] = self.opt_extract_ap.get()
        self.config["keep_ap_after_extract"] = self.opt_keep_ap.get()
        self.config["move_to_installed"] = self.opt_move_installed.get()
        save_config(self.config)

    def _format_size(self, size_bytes):
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024**3):.2f} GB"
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024**2):.1f} MB"
        if size_bytes >= 1024:
            return f"{size_bytes / 1024:.0f} KB"
        return f"{size_bytes} B"

    def _add_queue_item(self, item_path, item_type):
        norm = os.path.normpath(item_path)
        # Check duplicate
        for q in self.queue:
            if q["path"] == norm:
                return

        if item_type == "rwp":
            if not os.path.isfile(norm):
                return
            size = os.path.getsize(norm)
            name = os.path.splitext(os.path.basename(norm))[0]
            pkg_type = ".RWP Package"
        else:
            # folder
            if not os.path.isdir(norm):
                return
            size = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(norm) for f in fs)
            name = f"Extracted: {os.path.basename(norm)}"
            pkg_type = "Extracted Folder"

        item = {
            "path": norm,
            "name": name,
            "size": size,
            "type": item_type,
            "status": "Ready"
        }
        self.queue.append(item)
        self.queue_tree.insert("", tk.END, values=(name, self._format_size(size), pkg_type, "Ready", norm))

    def _add_rwp_files(self):
        initial_dir = self.config.get("last_source_dir", get_app_dir())
        files = filedialog.askopenfilenames(
            title="Select .rwp Addon Packages",
            initialdir=initial_dir,
            filetypes=[("Train Simulator Packages (*.rwp)", "*.rwp"), ("All Files", "*.*")]
        )
        if files:
            self.config["last_source_dir"] = os.path.dirname(files[0])
            save_config(self.config)
            for f in files:
                self._add_queue_item(f, "rwp")

    def _add_folder_rwp(self):
        initial_dir = self.config.get("last_source_dir", get_app_dir())
        folder = filedialog.askdirectory(title="Select Folder Containing .rwp Addons", initialdir=initial_dir)
        if folder:
            self.config["last_source_dir"] = folder
            save_config(self.config)
            count = 0
            for item in os.listdir(folder):
                if item.lower().endswith(".rwp"):
                    self._add_queue_item(os.path.join(folder, item), "rwp")
                    count += 1
            if count == 0:
                messagebox.showinfo("No .rwp Found", f"No .rwp files found in {folder}.")

    def _add_extracted_folder(self):
        initial_dir = self.config.get("last_source_dir", get_app_dir())
        folder = filedialog.askdirectory(title="Select Extracted Folder (Contains Assets/Content/Manuals)", initialdir=initial_dir)
        if folder:
            has_sub = any(os.path.isdir(os.path.join(folder, sf)) for sf in ["Assets", "Content", "Manuals"])
            if not has_sub:
                messagebox.showwarning("Warning", "The selected folder does not appear to have Assets, Content, or Manuals subdirectories.")
            self._add_queue_item(folder, "folder")

    def _clear_queue(self):
        if self.is_working:
            return
        self.queue.clear()
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        self.status_detail_lbl.config(text="Ready")
        self.progress_bar["value"] = 0

    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _update_tree_status(self, index, status_str):
        children = self.queue_tree.get_children()
        if 0 <= index < len(children):
            item_id = children[index]
            cur = list(self.queue_tree.item(item_id, "values"))
            cur[3] = status_str
            self.queue_tree.item(item_id, values=cur)

    def _start_installation(self):
        if self.is_working:
            return

        game_dir = self.game_dir_var.get().strip()
        if not is_valid_game_dir(game_dir):
            messagebox.showerror("Error", "Please provide a valid Train Simulator Classic directory (railworks) first.")
            return

        if not self.queue:
            messagebox.showinfo("Nothing to Install", "Please add .rwp files or extracted folders to the queue first.")
            return

        # Start thread
        self.is_working = True
        self.btn_install.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._run_install_worker, daemon=True)
        thread.start()

    def _run_install_worker(self):
        game_dir = self.game_dir_var.get().strip()
        seven_zip = self.seven_z_path_var.get().strip() or None

        options = {
            "extract_ap": self.opt_extract_ap.get(),
            "keep_ap_after_extract": self.opt_keep_ap.get(),
            "move_to_installed": self.opt_move_installed.get()
        }

        total_items = len(self.queue)
        success_count = 0

        self.root.after(0, lambda: self.log(f"=== Starting batch installation of {total_items} items ==="))

        for idx, item in enumerate(self.queue):
            if item["status"] == "Completed":
                continue

            self.root.after(0, lambda i=idx: self._update_tree_status(i, "Installing..."))
            self.root.after(0, lambda name=item["name"], i=idx: self.status_detail_lbl.config(
                text=f"[{i+1}/{total_items}] Installing {name}..."
            ))

            def progress_cb(msg, cur, tot):
                pct = int((cur / tot) * 100) if tot > 0 else 0
                self.root.after(0, lambda: self.progress_bar.configure(value=pct))
                self.root.after(0, lambda: self.status_detail_lbl.config(text=msg))

            def log_cb(msg):
                self.root.after(0, lambda: self.log(msg))

            success = False
            err_msg = ""
            try:
                if item["type"] == "rwp":
                    success, err_msg = install_rwp(
                        rwp_path=item["path"],
                        game_dir=game_dir,
                        options=options,
                        seven_zip=seven_zip,
                        progress_cb=progress_cb,
                        log_cb=log_cb
                    )
                else:
                    success, err_msg = install_extracted_folder(
                        source_folder=item["path"],
                        game_dir=game_dir,
                        options=options,
                        seven_zip=seven_zip,
                        progress_cb=progress_cb,
                        log_cb=log_cb
                    )
            except Exception as e:
                err_msg = str(e)
                success = False

            if success:
                success_count += 1
                item["status"] = "Completed"
                self.root.after(0, lambda i=idx: self._update_tree_status(i, "✓ Completed"))
            else:
                item["status"] = "Failed"
                self.root.after(0, lambda i=idx: self._update_tree_status(i, "✗ Failed"))
                self.root.after(0, lambda err=err_msg: self.log(f"[ERROR] {err}"))

        self.root.after(0, lambda: self.progress_bar.configure(value=100))
        self.root.after(0, lambda: self.status_detail_lbl.config(text=f"Batch complete: {success_count}/{total_items} installed successfully."))
        self.root.after(0, self._finish_installation, success_count, total_items)

    def _finish_installation(self, success_count, total_items):
        self.is_working = False
        self.btn_install.config(state=tk.NORMAL)
        self._refresh_history()
        messagebox.showinfo(
            "Installation Complete",
            f"Installation finished!\n\nSuccessfully installed: {success_count} / {total_items}\nCheck the 'Installation History' tab for tracked files."
        )

    # --- History Tab Methods ---

    def _refresh_history(self):
        records = self.history_mgr.load_history()
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        filter_text = self.search_var.get().strip().lower()

        for r in records:
            name = r.get("name", "")
            if filter_text and filter_text not in name.lower() and filter_text not in r.get("id", "").lower():
                continue

            status = r.get("status", "Installed")
            status_display = "✓ " + status if status == "Installed" else "✗ " + status
            self.hist_tree.insert(
                "",
                tk.END,
                values=(
                    name,
                    r.get("install_date", ""),
                    f"{r.get('file_count', 0):,}",
                    r.get("extracted_ap_count", 0),
                    f"{r.get('total_size_mb', 0):.1f}",
                    status_display,
                    r.get("id", "")
                )
            )

    def _filter_history(self):
        self._refresh_history()

    def _get_selected_mod_id(self):
        sel = self.hist_tree.selection()
        if not sel:
            return None
        values = self.hist_tree.item(sel[0], "values")
        return values[6]  # ID column

    def _view_manifest(self):
        mod_id = self._get_selected_mod_id()
        if not mod_id:
            messagebox.showinfo("Select Mod", "Please select a mod from the history table first.")
            return

        record = self.history_mgr.get_record(mod_id)
        if not record:
            messagebox.showerror("Error", "Could not locate record.")
            return

        # Show manifest dialog
        diag = tk.Toplevel(self.root)
        diag.title(f"Installed Manifest - {record.get('name')}")
        diag.geometry("750x520")
        diag.configure(bg=self.bg_color)

        lbl = tk.Label(diag, text=f"Installed Files ({record.get('file_count', 0)} files)", bg=self.bg_color, fg=self.accent_color, font=("Segoe UI", 11, "bold"))
        lbl.pack(anchor=tk.W, padx=12, pady=8)

        text_box = tk.Text(diag, bg="#11111b", fg=self.text_color, font=("Consolas", 9), relief="flat")
        scroll = ttk.Scrollbar(diag, orient=tk.VERTICAL, command=text_box.yview)
        text_box.configure(yscrollcommand=scroll.set)

        files = record.get("installed_files", [])
        for f in files:
            text_box.insert(tk.END, f + "\n")

        text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 12))
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=(0, 12))

    def _uninstall_selected_mod(self):
        mod_id = self._get_selected_mod_id()
        if not mod_id:
            messagebox.showinfo("Select Mod", "Please select a mod from the history table to uninstall.")
            return

        record = self.history_mgr.get_record(mod_id)
        if not record:
            return

        confirm = messagebox.askyesno(
            "Confirm Uninstallation",
            f"Are you sure you want to uninstall '{record.get('name')}'?\n\nThis will remove {record.get('file_count', 0)} tracked files from your RailWorks game folder."
        )
        if not confirm:
            return

        def uninst_thread():
            success, msg = self.history_mgr.uninstall_mod(mod_id)
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Uninstallation Complete", msg))
            else:
                self.root.after(0, lambda: messagebox.showerror("Uninstallation Error", msg))
            self.root.after(0, self._refresh_history)

        threading.Thread(target=uninst_thread, daemon=True).start()

    def _delete_record_only(self):
        mod_id = self._get_selected_mod_id()
        if not mod_id:
            messagebox.showinfo("Select Mod", "Please select a mod record to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Record Deletion",
            "Delete this record from installation history?\n(Note: This will NOT delete files from the game folder, only from the history log)."
        )
        if confirm:
            self.history_mgr.remove_record(mod_id)
            self._refresh_history()

    def _open_game_folder(self):
        game_dir = self.game_dir_var.get().strip()
        if os.path.isdir(game_dir):
            os.startfile(game_dir)
        else:
            messagebox.showwarning("Warning", "Game folder is not valid or does not exist.")

    # --- Batch Tools ---

    def _batch_unpack_ap(self):
        game_dir = self.game_dir_var.get().strip()
        if not is_valid_game_dir(game_dir):
            messagebox.showerror("Error", "Please configure a valid Train Simulator Classic directory first.")
            return

        confirm = messagebox.askyesno(
            "Confirm Batch .AP Unpack",
            "This will search all subfolders in your Train Simulator Assets and Content/Routes directories for packed .ap archives and extract their contents in place.\n\nDepending on your game library size, this may take a few minutes.\n\nDo you want to proceed?"
        )
        if not confirm:
            return

        seven_zip = self.seven_z_path_var.get().strip() or None

        def worker():
            self.root.after(0, lambda: self.log("=== Starting Batch .AP Unpack Scan ==="))
            ap_files = []
            for sub in ["Assets", "Content"]:
                root_sub = os.path.join(game_dir, sub)
                if os.path.isdir(root_sub):
                    for r, d, fs in os.walk(root_sub):
                        for f in fs:
                            if f.lower().endswith(".ap"):
                                ap_files.append(os.path.join(r, f))

            total = len(ap_files)
            self.root.after(0, lambda: self.log(f"Found {total} .ap archives in game directory."))
            if total == 0:
                self.root.after(0, lambda: messagebox.showinfo("No .AP Files", "No .ap archives were found."))
                return

            unpacked = 0
            for idx, ap_path in enumerate(ap_files):
                parent_dir = os.path.dirname(ap_path)
                ap_name = os.path.basename(ap_path)
                self.root.after(0, lambda msg=f"[{idx+1}/{total}] Unpacking {ap_name}...": self.status_detail_lbl.config(text=msg))
                self.root.after(0, lambda msg=f"Unpacking {ap_name} into {os.path.relpath(parent_dir, game_dir)}": self.log(msg))
                try:
                    extract_archive(ap_path, parent_dir, seven_zip)
                    unpacked += 1
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self.log(f"Error unpacking {ap_name}: {err}"))

            self.root.after(0, lambda: self.log(f"=== Finished batch unpacking: {unpacked}/{total} archives extracted. ==="))
            self.root.after(0, lambda: messagebox.showinfo("Batch Complete", f"Successfully unpacked {unpacked} / {total} .ap archives!"))

        threading.Thread(target=worker, daemon=True).start()

def run_gui():
    root = tk.Tk()
    app = ModernRWPInstallerApp(root)
    root.mainloop()

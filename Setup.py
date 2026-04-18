"""
AniDex Setup & Uninstall Wizard
────────────────────────────────────────────────────────────────────────────
Dual-purpose compiler:
  - Run normally: Acts as the Setup Wizard.
  - Run with '--uninstall': Acts as the Uninstall Wizard.
"""

import os, sys, zipfile, subprocess, threading, time, shutil, winreg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
APP_NAME       = "AniDex"
APP_VERSION    = "2.0"
APP_PUBLISHER  = "AniDex Project"
ZIP_FILE_NAME  = "AniDex.zip"
APP_EXE_NAME   = "AniDex.exe"
UNINSTALL_EXE  = "Uninstall AniDex.exe" 
REG_SUBKEY     = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AniDex"

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE 
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":       "#080b14",
    "sidebar":  "#0c1020",
    "surface":  "#111827",
    "surface2": "#1a2235",
    "surface3": "#222d42",
    "border":   "#1e2d47",
    "accent":   "#e8383d",
    "text":     "#e8eaf0",
    "text_mid": "#8b95b0",
    "text_dim": "#4a5568",
    "white":    "#ffffff",
    "green":    "#10b981",
}

F = {
    "big":    ("Georgia",     18, "bold"),
    "title":  ("Georgia",     13, "bold"),
    "body":   ("Courier New", 10),
    "small":  ("Courier New",  9),
    "label":  ("Courier New",  8, "bold"),
    "btn":    ("Courier New",  9, "bold"),
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def resource_path(rel):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, rel)


def create_shortcut(target_path, shortcut_path, icon_path=None):
    working_dir = os.path.dirname(target_path)
    vbs = os.path.join(os.environ["TEMP"], "_anidex_shortcut.vbs")
    lines = [
        'Set oWS = WScript.CreateObject("WScript.Shell")',
        f'Set oLink = oWS.CreateShortcut("{shortcut_path}")',
        f'oLink.TargetPath = "{target_path}"',
        f'oLink.WorkingDirectory = "{working_dir}"',
    ]
    if icon_path and os.path.exists(icon_path):
        lines.append(f'oLink.IconLocation = "{icon_path}"')
    lines.append("oLink.Save")
    with open(vbs, "w") as f:
        f.write("\n".join(lines))
    subprocess.run(["cscript", "//nologo", vbs], shell=True, creationflags=0x08000000)
    try: os.remove(vbs)
    except OSError: pass


def write_registry_entry(install_dir, uninstaller_path):
    exe_path  = os.path.join(install_dir, APP_EXE_NAME)
    icon_path = os.path.join(install_dir, "ramen.ico")

    values = {
        "DisplayName":          APP_NAME,
        "DisplayVersion":       APP_VERSION,
        "Publisher":            APP_PUBLISHER,
        "InstallLocation":      install_dir,
        "DisplayIcon":          icon_path if os.path.exists(icon_path) else exe_path,
        "UninstallString":      f'"{uninstaller_path}" --uninstall',
        "QuietUninstallString": f'"{uninstaller_path}" --uninstall',
        "NoModify":             1,   
        "NoRepair":             1,   
        "EstimatedSize":        _estimate_kb(install_dir),
    }

    for hive, hive_name in [(winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER,  "HKCU")]:
        try:
            key = winreg.CreateKeyEx(hive, REG_SUBKEY, 0, winreg.KEY_SET_VALUE)
            for name, val in values.items():
                if isinstance(val, int):
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, val)
                else:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
            winreg.CloseKey(key)
            return hive_name   
        except PermissionError:
            continue
    raise PermissionError("Could not write to registry (HKLM or HKCU).")


def _estimate_kb(folder):
    total = 0
    for dirpath, _, files in os.walk(folder):
        for f in files:
            try: total += os.path.getsize(os.path.join(dirpath, f))
            except OSError: pass
    return max(1, total // 1024)


def is_already_installed():
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            k = winreg.OpenKey(hive, REG_SUBKEY)
            winreg.CloseKey(k)
            return True
        except FileNotFoundError:
            pass
    return False

# ─────────────────────────────────────────────────────────────────────────────
# HOVER BUTTON  
# ─────────────────────────────────────────────────────────────────────────────
class HoverBtn(tk.Label):
    def __init__(self, parent, text, cmd, bg, fg, hbg=None, hfg=None, **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, cursor="hand2", **kw)
        self._bg = bg; self._fg = fg
        self._hbg = hbg or C["accent"]; self._hfg = hfg or C["white"]
        self._cmd = cmd
        self.bind("<Enter>",           lambda _: self.configure(bg=self._hbg, fg=self._hfg))
        self.bind("<Leave>",           lambda _: self.configure(bg=self._bg,  fg=self._fg))
        self.bind("<ButtonRelease-1>", lambda _: self._cmd())

# ─────────────────────────────────────────────────────────────────────────────
# UI BASE WIZARD (Shared UI structure for Setup and Uninstall)
# ─────────────────────────────────────────────────────────────────────────────
class BaseWizard(tk.Tk):
    def __init__(self, title_text):
        super().__init__()
        self.title(title_text)
        self.geometry("540x380")
        self.resizable(False, False)
        self.configure(bg=C["bg"])

        ico = resource_path("ramen.ico")
        if os.path.exists(ico):
            try: self.iconbitmap(ico)
            except Exception: pass

        self._pages = {}
        self._container = tk.Frame(self, bg=C["bg"])
        self._container.pack(fill=tk.BOTH, expand=True)

    def _build_bottom_bar(self, dots_count=0):
        sep = tk.Frame(self, bg=C["border"], height=1)
        sep.pack(fill=tk.X)
        bar = tk.Frame(self, bg=C["surface"], pady=10)
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        self._btn_cancel = HoverBtn(bar, "Cancel", self.destroy, bg=C["surface3"], fg=C["text_mid"], hbg=C["surface2"], hfg=C["text"], font=F["btn"], padx=14, pady=6)
        self._btn_cancel.pack(side=tk.RIGHT, padx=(4, 16))

        self._btn_next = HoverBtn(bar, "Next >", lambda: None, bg=C["accent"], fg=C["white"], hbg="#ff5055", hfg=C["white"], font=F["btn"], padx=14, pady=6)
        self._btn_next.pack(side=tk.RIGHT, padx=4)

        self._btn_back = HoverBtn(bar, "< Back", lambda: None, bg=C["surface3"], fg=C["text_mid"], hbg=C["surface2"], hfg=C["text"], font=F["btn"], padx=14, pady=6)
        self._btn_back.pack(side=tk.RIGHT, padx=4)

        self._dot_frame = tk.Frame(bar, bg=C["surface"])
        self._dot_frame.pack(side=tk.LEFT, padx=16)
        self._dots = []
        for _ in range(dots_count):
            d = tk.Label(self._dot_frame, text="●", bg=C["surface"], fg=C["text_dim"], font=("Courier New", 8))
            d.pack(side=tk.LEFT, padx=2)
            self._dots.append(d)

    def _update_dots(self, active):
        for i, d in enumerate(self._dots):
            d.configure(fg=C["accent"] if i == active else C["text_dim"])

    def _sidebar_page(self, key):
        frame = tk.Frame(self._container, bg=C["bg"])
        self._pages[key] = frame
        sb = tk.Frame(frame, bg=C["sidebar"], width=155)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)
        tk.Label(sb, text="彡", bg=C["sidebar"], fg=C["accent"], font=("Georgia", 36)).pack(pady=(40, 4))
        tk.Label(sb, text=APP_NAME, bg=C["sidebar"], fg=C["text"], font=("Georgia", 12, "bold")).pack()
        tk.Label(sb, text=f"v{APP_VERSION}", bg=C["sidebar"], fg=C["text_dim"], font=F["small"]).pack(pady=(2, 0))
        right = tk.Frame(frame, bg=C["bg"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return frame, right

    def _banner_page(self, key, heading):
        frame = tk.Frame(self._container, bg=C["bg"])
        self._pages[key] = frame
        banner = tk.Frame(frame, bg=C["surface"], height=58)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)
        tk.Frame(banner, bg=C["accent"], height=3).pack(fill=tk.X, side=tk.TOP)
        tk.Label(banner, text=heading, bg=C["surface"], fg=C["text"], font=F["title"], anchor="w").pack(fill=tk.X, padx=20, pady=(10, 0))
        tk.Frame(frame, bg=C["border"], height=1).pack(fill=tk.X)
        body = tk.Frame(frame, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=18)
        return frame, body

    def _show(self, page):
        for f in self._pages.values(): f.pack_forget()
        self._pages[page].pack(fill=tk.BOTH, expand=True)

    def _set_buttons(self, back=True, next_=True, cancel=True, next_label="Next >"):
        self._btn_back.configure(fg=C["text_mid"] if back else C["text_dim"], cursor="hand2" if back else "arrow")
        self._btn_back._cmd = getattr(self, "_go_back", lambda: None) if back else lambda: None

        self._btn_next.configure(bg=C["accent"] if next_ else C["surface3"], fg=C["white"] if next_ else C["text_dim"], text=next_label, cursor="hand2" if next_ else "arrow")
        self._btn_next._cmd = getattr(self, "_go_next", lambda: None) if next_ else lambda: None

        self._btn_cancel.configure(fg=C["text_mid"] if cancel else C["text_dim"], cursor="hand2" if cancel else "arrow")
        self._btn_cancel._cmd = self.destroy if cancel else lambda: None


# ─────────────────────────────────────────────────────────────────────────────
# SETUP WIZARD
# ─────────────────────────────────────────────────────────────────────────────
class SetupWizard(BaseWizard):
    def __init__(self):
        super().__init__(f"{APP_NAME} Setup")
        self._step = 0
        self.install_path = tk.StringVar(value=os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), APP_NAME))
        self.desktop_shortcut = tk.BooleanVar(value=True)
        self.launch_after = tk.BooleanVar(value=True)

        self._build_bottom_bar(dots_count=4)
        self._page_welcome()
        self._page_already()
        self._page_path()
        self._page_install()
        self._page_finish()

        if is_already_installed():
            self._show("AlreadyInstalled")
            self._set_buttons(back=False, next_=False, cancel=True, next_label="Next >")
            self._btn_cancel.configure(text="Exit", command=self.destroy)
        else:
            self._show("Welcome")
            self._set_buttons(back=False, next_=True, cancel=True)

    def _page_welcome(self):
        _, right = self._sidebar_page("Welcome")
        tk.Label(right, text=f"Welcome to\n{APP_NAME} Setup", bg=C["bg"], fg=C["text"], font=F["big"], justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=20, pady=(30, 16))
        tk.Frame(right, bg=C["border"], height=1).pack(fill=tk.X, padx=20)
        tk.Label(right, text=(f"This wizard will guide you through the\ninstallation of {APP_NAME} {APP_VERSION}.\n\nClick Next to continue, or Cancel to exit."), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=320).pack(fill=tk.X, padx=20, pady=16)

    def _page_already(self):
        _, right = self._sidebar_page("AlreadyInstalled")
        tk.Label(right, text=f"{APP_NAME} is\nalready installed", bg=C["bg"], fg=C["accent"], font=F["big"], justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=20, pady=(30, 16))
        tk.Frame(right, bg=C["border"], height=1).pack(fill=tk.X, padx=20)
        tk.Label(right, text=("A previous installation was detected.\n\nTo reinstall or update, please first uninstall\n{APP_NAME} via Control Panel → Programs,\nthen run this setup again.\n\nClick Exit to close."), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=320).pack(fill=tk.X, padx=20, pady=16)

    def _page_path(self):
        _, body = self._banner_page("Path", "Choose Install Location")
        tk.Label(body, text=("Setup will install AniDex in the folder below.\nTo change it, click Browse."), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=430).pack(fill=tk.X, pady=(0, 14))
        tk.Label(body, text="DESTINATION FOLDER", bg=C["bg"], fg=C["text_dim"], font=F["label"]).pack(anchor="w")
        pf = tk.Frame(body, bg=C["bg"])
        pf.pack(fill=tk.X, pady=(4, 0))
        path_entry = tk.Entry(pf, textvariable=self.install_path, bg=C["surface2"], fg=C["text"], insertbackground=C["accent"], relief="flat", font=F["body"], highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["accent"])
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        HoverBtn(pf, "  Browse…  ", self._browse, bg=C["surface3"], fg=C["text_mid"], hbg=C["surface2"], hfg=C["text"], font=F["btn"], padx=10, pady=6).pack(side=tk.LEFT, padx=(8, 0))
        self._space_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._space_var, bg=C["bg"], fg=C["text_dim"], font=F["small"]).pack(anchor="w", pady=(10, 0))
        self._update_space_estimate()

    def _update_space_estimate(self):
        zip_path = resource_path(ZIP_FILE_NAME)
        if os.path.exists(zip_path):
            mb = os.path.getsize(zip_path) / (1024 * 1024)
            self._space_var.set(f"Estimated disk space required: ~{mb:.1f} MB")

    def _page_install(self):
        _, body = self._banner_page("Install", "Installing…")
        self._status_var = tk.StringVar(value="Preparing…")
        tk.Label(body, textvariable=self._status_var, bg=C["bg"], fg=C["text_mid"], font=F["body"], anchor="w").pack(fill=tk.X, pady=(10, 6))
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Dark.Horizontal.TProgressbar", troughcolor=C["surface2"], background=C["accent"], borderwidth=0)
        self._prog_var = tk.DoubleVar()
        ttk.Progressbar(body, variable=self._prog_var, maximum=100, style="Dark.Horizontal.TProgressbar", length=460).pack(fill=tk.X)
        self._prog_label = tk.StringVar(value="")
        tk.Label(body, textvariable=self._prog_label, bg=C["bg"], fg=C["text_dim"], font=F["small"], anchor="w").pack(fill=tk.X, pady=(4, 0))
        self._log_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._log_var, bg=C["bg"], fg=C["text_dim"], font=F["small"], anchor="w", justify=tk.LEFT).pack(fill=tk.X, pady=(14, 0))

    def _page_finish(self):
        _, right = self._sidebar_page("Finish")
        tk.Label(right, text="Installation\nComplete!", bg=C["bg"], fg=C["green"], font=F["big"], justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=20, pady=(30, 16))
        tk.Frame(right, bg=C["border"], height=1).pack(fill=tk.X, padx=20)
        tk.Label(right, text=(f"{APP_NAME} has been installed successfully.\n\nTo remove it later, go to:\nControl Panel → Programs → Uninstall a program"), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=310).pack(fill=tk.X, padx=20, pady=(14, 10))
        opts = tk.Frame(right, bg=C["bg"])
        opts.pack(fill=tk.X, padx=20)
        for var, lbl in [(self.desktop_shortcut, "Create a Desktop shortcut"), (self.launch_after, f"Launch {APP_NAME} after finishing")]:
            cb = tk.Checkbutton(opts, text=lbl, variable=var, bg=C["bg"], fg=C["text_mid"], selectcolor=C["surface2"], activebackground=C["bg"], activeforeground=C["text"], font=F["body"], cursor="hand2")
            cb.pack(anchor="w", pady=2)

    def _go_back(self):
        if self._step == 1:
            self._step = 0
            self._show("Welcome")
            self._set_buttons(back=False, next_=True, cancel=True)
            self._update_dots(0)

    def _go_next(self):
        if self._step == 0:
            self._step = 1
            self._show("Path")
            self._set_buttons(back=True, next_=True, cancel=True)
            self._update_dots(1)
        elif self._step == 1:
            dest = self.install_path.get().strip()
            if not dest: return messagebox.showerror("Error", "Please choose an installation folder.")
            self._step = 2
            self._show("Install")
            self._set_buttons(back=False, next_=False, cancel=False)
            self._update_dots(2)
            threading.Thread(target=self._run_install, daemon=True).start()
        elif self._step == 3:          
            self._do_finish()

    def _set_progress(self, text, value, detail=""):
        self.after(0, lambda: self._status_var.set(text))
        self.after(0, lambda: self._prog_var.set(value))
        self.after(0, lambda: self._prog_label.set(f"{int(value)}%"))
        if detail: self.after(0, lambda: self._log_var.set(f"→ {detail}"))

    def _run_install(self):
        try:
            dest = self.install_path.get().strip()
            zip_src = resource_path(ZIP_FILE_NAME)

            self._set_progress("Creating destination folder…", 5)
            os.makedirs(dest, exist_ok=True)

            self._set_progress("Locating installer bundle…", 12)
            if not os.path.exists(zip_src): raise FileNotFoundError("Bundle missing.")

            self._set_progress("Extracting files…", 20)
            with zipfile.ZipFile(zip_src, "r") as zf:
                entries = zf.namelist()
                for i, entry in enumerate(entries):
                    zf.extract(entry, dest)
                    self._set_progress("Extracting files…", 20 + (i + 1) / len(entries) * 55, entry)

            ico_src = resource_path("ramen.ico")
            if os.path.exists(ico_src): shutil.copy2(ico_src, os.path.join(dest, "ramen.ico"))

            # MAGIC TRICK: Copy the setup.exe itself into the install folder to act as Uninstaller
            self._set_progress("Configuring Uninstaller…", 80)
            uninstaller_path = os.path.join(dest, UNINSTALL_EXE)
            if getattr(sys, 'frozen', False):
                shutil.copy2(sys.executable, uninstaller_path)
            else:
                shutil.copy2(os.path.abspath(__file__), uninstaller_path)

            self._set_progress("Registering with Windows…", 88, "Writing uninstall entry…")
            write_registry_entry(dest, uninstaller_path)

            self._set_progress("Creating Start Menu entry…", 93)
            self._make_start_menu(dest)

            self._set_progress("Finishing up…", 100)
            time.sleep(0.4)
            self.after(0, self._install_done)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, self.destroy)

    def _make_start_menu(self, install_dir):
        exe = self._find_exe(install_dir)
        smdir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs", APP_NAME)
        os.makedirs(smdir, exist_ok=True)
        if exe: create_shortcut(exe, os.path.join(smdir, f"{APP_NAME}.lnk"), os.path.join(install_dir, "ramen.ico"))

    def _find_exe(self, install_dir):
        for root, _, files in os.walk(install_dir):
            if APP_EXE_NAME in files: return os.path.join(root, APP_EXE_NAME)
        return None

    def _install_done(self):
        self._step = 3
        self._show("Finish")
        self._set_buttons(back=False, next_=True, cancel=False, next_label="Finish")
        self._update_dots(3)

    def _do_finish(self):
        install_dir = self.install_path.get().strip()
        exe = self._find_exe(install_dir)
        if self.desktop_shortcut.get() and exe:
            try: create_shortcut(exe, os.path.join(os.path.expanduser("~"), "Desktop", f"{APP_NAME}.lnk"), os.path.join(install_dir, "ramen.ico"))
            except Exception: pass
        if self.launch_after.get() and exe:
            try: subprocess.Popen([exe], cwd=os.path.dirname(exe), creationflags=0x00000008)
            except Exception: pass
        self.destroy()
        
    def _browse(self):
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder: self.install_path.set(folder.replace("/", "\\"))


# ─────────────────────────────────────────────────────────────────────────────
# UNINSTALL WIZARD
# ─────────────────────────────────────────────────────────────────────────────
class UninstallWizard(BaseWizard):
    def __init__(self, install_dir):
        super().__init__(f"{APP_NAME} Uninstall")
        self.install_dir = install_dir
        self._step = 0

        self._build_bottom_bar(dots_count=3)
        self._page_welcome()
        self._page_progress()
        self._page_finish()

        self._show("Welcome")
        self._set_buttons(back=False, next_=True, cancel=True, next_label="Uninstall")

    def _page_welcome(self):
        _, right = self._sidebar_page("Welcome")
        tk.Label(right, text=f"Uninstall\n{APP_NAME}", bg=C["bg"], fg=C["accent"], font=F["big"], justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=20, pady=(30, 16))
        tk.Frame(right, bg=C["border"], height=1).pack(fill=tk.X, padx=20)
        tk.Label(right, text=(f"You are about to completely remove {APP_NAME} and all of its components from your computer.\n\nAre you sure you want to proceed?"), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=320).pack(fill=tk.X, padx=20, pady=16)

    def _page_progress(self):
        _, body = self._banner_page("Progress", "Removing Files…")
        self._status_var = tk.StringVar(value="Preparing to uninstall…")
        tk.Label(body, textvariable=self._status_var, bg=C["bg"], fg=C["text_mid"], font=F["body"], anchor="w").pack(fill=tk.X, pady=(10, 6))
        s = ttk.Style(); s.theme_use("clam")
        s.configure("Dark.Horizontal.TProgressbar", troughcolor=C["surface2"], background=C["accent"], borderwidth=0)
        self._prog_var = tk.DoubleVar()
        ttk.Progressbar(body, variable=self._prog_var, maximum=100, style="Dark.Horizontal.TProgressbar", length=460).pack(fill=tk.X)
        self._log_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._log_var, bg=C["bg"], fg=C["text_dim"], font=F["small"], anchor="w", justify=tk.LEFT).pack(fill=tk.X, pady=(14, 0))

    def _page_finish(self):
        _, right = self._sidebar_page("Finish")
        tk.Label(right, text="Uninstall\nComplete", bg=C["bg"], fg=C["green"], font=F["big"], justify=tk.LEFT, anchor="w").pack(fill=tk.X, padx=20, pady=(30, 16))
        tk.Frame(right, bg=C["border"], height=1).pack(fill=tk.X, padx=20)
        tk.Label(right, text=(f"{APP_NAME} was successfully removed from your computer.\n\nClick Close to exit."), bg=C["bg"], fg=C["text_mid"], font=F["body"], justify=tk.LEFT, wraplength=320).pack(fill=tk.X, padx=20, pady=16)

    def _go_next(self):
        if self._step == 0:
            self._step = 1
            self._show("Progress")
            self._set_buttons(back=False, next_=False, cancel=False)
            self._update_dots(1)
            threading.Thread(target=self._run_uninstall, daemon=True).start()
        elif self._step == 2:
            self._trigger_self_destruct()
            self.destroy()

    def _set_progress(self, text, value, detail=""):
        self.after(0, lambda: self._status_var.set(text))
        self.after(0, lambda: self._prog_var.set(value))
        if detail: self.after(0, lambda: self._log_var.set(f"→ {detail}"))

    def _run_uninstall(self):
        try:
            # 1. Remove Registry Keys
            self._set_progress("Cleaning Registry...", 20, "Removing Control Panel entries")
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try: winreg.DeleteKey(hive, REG_SUBKEY)
                except Exception: pass

            # 2. Remove Shortcuts
            self._set_progress("Removing Shortcuts...", 40, "Cleaning Start Menu and Desktop")
            smdir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs", APP_NAME)
            if os.path.exists(smdir): shutil.rmtree(smdir, ignore_errors=True)
            
            desktop_lnk = os.path.join(os.path.expanduser("~"), "Desktop", f"{APP_NAME}.lnk")
            if os.path.exists(desktop_lnk): 
                try: os.remove(desktop_lnk)
                except OSError: pass

            # 3. Delete App Files (Except the running Uninstaller)
            self._set_progress("Deleting App Files...", 70, "Emptying installation directory")
            if os.path.exists(self.install_dir):
                for item in os.listdir(self.install_dir):
                    item_path = os.path.join(self.install_dir, item)
                    # Don't delete ourselves while running!
                    if item.lower() != UNINSTALL_EXE.lower():
                        try:
                            if os.path.isdir(item_path): shutil.rmtree(item_path)
                            else: os.path.remove(item_path)
                        except Exception: pass

            self._set_progress("Finalizing...", 100, "")
            time.sleep(0.5)
            self.after(0, self._uninstall_done)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Uninstall Error", str(e)))
            self.after(0, self.destroy)

    def _uninstall_done(self):
        self._step = 2
        self._show("Finish")
        self._set_buttons(back=False, next_=True, cancel=False, next_label="Close")
        self._update_dots(2)

    def _trigger_self_destruct(self):
        """ Secretly drops a temp script that deletes the empty folder from the outside AFTER the UI closes """
        bat_path = os.path.join(os.environ["TEMP"], "_anidex_cleanup.bat")
        lines = [
            "@echo off",
            "timeout /t 2 /nobreak >nul", # Wait 2 seconds for Python to close
            f'rmdir /s /q "{self.install_dir}"', # Delete the folder and the uninstaller inside it
            f'del "%~f0"' # Delete this temp bat file
        ]
        with open(bat_path, "w") as f:
            f.write("\n".join(lines))
        subprocess.Popen(['cmd', '/c', bat_path], creationflags=0x08000000)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # If launched with the uninstall flag, boot the Uninstall Wizard!
    if "--uninstall" in sys.argv:
        current_dir = os.path.dirname(sys.executable)
        app = UninstallWizard(current_dir)
        app.mainloop()
    else:
        app = SetupWizard()
        app.mainloop()
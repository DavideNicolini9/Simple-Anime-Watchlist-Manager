import os
import sys
import zipfile
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# --- CONFIGURATION ---
ZIP_FILE_NAME = "AnimeWatchList_GUI.zip"  # The name of the zip file you bundle
APP_EXE_NAME = "AnimeWatchList_GUI.exe" # The name of the executable inside the zip

def resource_path(relative_path):
    """ Get absolute path to resource (looks in the invisible temp folder) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_shortcut(target_path, shortcut_path):
    # Get the folder where the .exe actually lives
    working_dir = os.path.dirname(target_path)
    
    vbs_script = os.path.join(os.environ['TEMP'], 'createshortcut.vbs')
    with open(vbs_script, 'w') as f:
        f.write('Set oWS = WScript.CreateObject("WScript.Shell")\n')
        f.write(f'sLinkFile = "{shortcut_path}"\n')
        f.write('Set oLink = oWS.CreateShortcut(sLinkFile)\n')
        f.write(f'oLink.TargetPath = "{target_path}"\n')
        
        # THIS IS THE MAGIC LINE: Set the "Start in" folder
        f.write(f'oLink.WorkingDirectory = "{working_dir}"\n') 
        
        f.write('oLink.Save\n')
        
    CREATE_NO_WINDOW = 0x08000000
    subprocess.run(['cscript', '//nologo', vbs_script], shell=True, creationflags=CREATE_NO_WINDOW)
    os.remove(vbs_script)

class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Anime Tracker Setup")
        self.geometry("500x360")
        self.resizable(False, False)
        
        try:
            self.iconbitmap(resource_path('ramen.ico'))
        except Exception:
            pass

        self.current_step = 0
        
        # Set default path to C:\Program Files (x86)\AnimeTracker
        default_dir = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        self.install_path = tk.StringVar(value=os.path.join(default_dir, "AnimeTracker"))
        
        self.create_shortcut_var = tk.BooleanVar(value=True) # Checkbox variable
        
        # --- Bottom Button Bar ---
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(self.bottom_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = tk.Frame(self.bottom_frame)
        btn_frame.pack(side=tk.RIGHT, padx=15, pady=(0, 15))
        
        self.btn_back = tk.Button(btn_frame, text="< Back", width=10, command=self.go_back)
        self.btn_back.pack(side=tk.LEFT, padx=2)
        
        self.btn_next = tk.Button(btn_frame, text="Next >", width=10, command=self.go_next)
        self.btn_next.pack(side=tk.LEFT, padx=2)
        
        self.btn_cancel = tk.Button(btn_frame, text="Cancel", width=10, command=self.destroy)
        self.btn_cancel.pack(side=tk.LEFT, padx=(10, 0))

        # --- Main Content Area ---
        self.container = tk.Frame(self)
        self.container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.pages = {}
        self.create_welcome_page()
        self.create_path_page()
        self.create_install_page()
        self.create_finish_page()
        
        self.show_page("Welcome")

    def show_page(self, page_name):
        for frame in self.pages.values():
            frame.pack_forget()
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)

    # --- Page 1: Welcome ---
    def create_welcome_page(self):
        frame = tk.Frame(self.container, bg="white")
        self.pages["Welcome"] = frame
        sidebar = tk.Frame(frame, bg="#000080", width=160)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        right_area = tk.Frame(frame, bg="white")
        right_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(right_area, text="Welcome to the Anime Tracker\nSetup Wizard", font=("Arial", 14, "bold"), bg="white", justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(0, 20))
        tk.Label(right_area, text="This wizard will guide you through the installation of Anime Tracker on your computer.\n\nClick Next to continue.", font=("Arial", 9), bg="white", justify=tk.LEFT, wraplength=300).pack(fill=tk.X)

    # --- Page 2: Choose Path ---
    def create_path_page(self):
        frame = tk.Frame(self.container)
        self.pages["Path"] = frame
        banner = tk.Frame(frame, bg="white", height=60)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)
        tk.Label(banner, text="Choose Install Location", font=("Arial", 10, "bold"), bg="white", anchor="w").pack(fill=tk.X, padx=15, pady=(10, 2))
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        body = tk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(body, text="Setup will install Anime Tracker in the following folder. To install in a different folder, click Browse and select another folder. Click Next to continue.", wraplength=450, justify=tk.LEFT).pack(fill=tk.X, pady=(0, 15))
        
        path_frame = tk.Frame(body)
        path_frame.pack(fill=tk.X)
        tk.Label(path_frame, text="Destination Folder:").pack(anchor="w")
        tk.Entry(path_frame, textvariable=self.install_path, width=45).pack(side=tk.LEFT, pady=5)
        tk.Button(path_frame, text="Browse...", command=self.browse_path).pack(side=tk.LEFT, padx=10)

    # --- Page 3: Installing (Progress Bar) ---
    def create_install_page(self):
        frame = tk.Frame(self.container)
        self.pages["Install"] = frame
        banner = tk.Frame(frame, bg="white", height=60)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)
        tk.Label(banner, text="Installing", font=("Arial", 10, "bold"), bg="white", anchor="w").pack(fill=tk.X, padx=15, pady=(10, 2))
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        body = tk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.status_label = tk.Label(body, text="Preparing to install...", anchor="w")
        self.status_label.pack(fill=tk.X, pady=(20, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(body, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)

    # --- Page 4: Finish ---
    def create_finish_page(self):
        frame = tk.Frame(self.container, bg="white")
        self.pages["Finish"] = frame
        sidebar = tk.Frame(frame, bg="#000080", width=160)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        right_area = tk.Frame(frame, bg="white")
        right_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(right_area, text="Completing the Setup Wizard", font=("Arial", 14, "bold"), bg="white", justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(0, 20))
        tk.Label(right_area, text="Anime Tracker has been successfully installed on your computer.\n\nClick Finish to close this wizard.", font=("Arial", 9), bg="white", justify=tk.LEFT, wraplength=300).pack(fill=tk.X, pady=(0, 20))
        
        # Checkbox for Desktop Shortcut
        tk.Checkbutton(right_area, text="Create a desktop shortcut", variable=self.create_shortcut_var, bg="white", activebackground="white").pack(anchor="w")

    # --- Actions & Logic ---
    def browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.install_path.get())
        if folder:
            self.install_path.set(folder)

    def go_back(self):
        if self.current_step == 1:
            self.current_step = 0
            self.btn_back.config(state=tk.DISABLED)
            self.show_page("Welcome")

    def go_next(self):
        if self.current_step == 0:
            self.current_step = 1
            self.btn_back.config(state=tk.NORMAL)
            self.show_page("Path")
            
        elif self.current_step == 1:
            self.current_step = 2
            self.btn_back.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            self.btn_cancel.config(state=tk.DISABLED)
            self.show_page("Install")
            threading.Thread(target=self.run_installation, daemon=True).start()
            
        elif self.current_step == 3:
            # Evaluate the checkbox right before closing
            if self.create_shortcut_var.get():
                install_dir = self.install_path.get()
                target_app = None
                
                # SMART SEARCH: Search every folder and subfolder for the .exe
                for root_dir, dirs, files in os.walk(install_dir):
                    if APP_EXE_NAME in files:
                        target_app = os.path.join(root_dir, APP_EXE_NAME)
                        break # Stop searching once we find it
                        
                if target_app:
                    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                    shortcut_path = os.path.join(desktop_dir, "AnimeWatchList_GUI.lnk")  #here
                    try:
                        create_shortcut(target_app, shortcut_path)
                    except Exception as e:
                        messagebox.showwarning("Shortcut Error", f"Failed to create shortcut:\n{str(e)}")
                else:
                    messagebox.showwarning("Shortcut Error", f"Could not find '{APP_EXE_NAME}' inside the extracted files.\nShortcut could not be created.")
            
            self.destroy()
            
        elif self.current_step == 1:
            self.current_step = 2
            self.btn_back.config(state=tk.DISABLED)
            self.btn_next.config(state=tk.DISABLED)
            self.btn_cancel.config(state=tk.DISABLED)
            self.show_page("Install")
            threading.Thread(target=self.run_installation, daemon=True).start()
            
        elif self.current_step == 3:
            # Evaluate the checkbox right before closing
            if self.create_shortcut_var.get():
                target_app = os.path.join(self.install_path.get(), APP_EXE_NAME)
                desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_dir, "AnimeWatchList_GUI.lnk")
                try:
                    create_shortcut(target_app, shortcut_path)
                except Exception as e:
                    messagebox.showwarning("Shortcut Error", f"Failed to create shortcut:\n{str(e)}")
            self.destroy()

    def run_installation(self):
        try:
            target_dir = self.install_path.get()
            zip_path = resource_path(ZIP_FILE_NAME)
            
            # 1. Create Destination Folder
            self.update_progress("Creating destination folder...", 10)
            time.sleep(0.5)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            # 2. Open and Extract the Zip file
            self.update_progress("Extracting files...", 30)
            if not os.path.exists(zip_path):
                raise Exception(f"Could not find {ZIP_FILE_NAME} inside the installer.\nMake sure it is added via 'Additional Files'.")
                
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                total_files = len(files)
                
                for i, file in enumerate(files):
                    zip_ref.extract(file, target_dir)
                    # Update progress bar smoothly based on files extracted
                    progress = 30 + ((i + 1) / total_files) * 60
                    self.update_progress(f"Extracting: {file}", progress)
            
            self.update_progress("Finishing up...", 100)
            time.sleep(0.5)
            
            self.after(0, self.finish_installation)
            
        except PermissionError:
            self.after(0, lambda: messagebox.showerror("Permission Denied", "Installation failed!\n\nYou need Administrator privileges to install to 'Program Files'. Please run this setup as an Administrator."))
            self.after(0, self.destroy)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Installation Error", str(e)))
            self.after(0, self.destroy)

    def update_progress(self, text, value):
        self.after(0, lambda: self.status_label.config(text=text))
        self.after(0, lambda: self.progress_var.set(value))

    def finish_installation(self):
        self.current_step = 3
        self.btn_next.config(state=tk.NORMAL, text="Finish")
        self.btn_cancel.config(state=tk.DISABLED)
        self.show_page("Finish")

if __name__ == "__main__":
    app = SetupWizard()
    app.btn_back.config(state=tk.DISABLED)
    app.mainloop()
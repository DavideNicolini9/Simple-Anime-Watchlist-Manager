import sqlite3
import os
import sys
import glob
import tkinter as tk
from tkinter import ttk, messagebox

DB_NAME = 'AnimeWatchList'
TABLE_NAME = 'ANIME'

"""
To create .exe from this code:
- open cmd in the same directory of this code
- run "auto-py-to-exe" (if not installed "pip install auto-py-to-exe")
- select the script
- select "One file"
- in the Icon menu, select .ico file
- in the Additional Files menu, add the path of the .ico
- clik on the "Convert .py to .exe" tab
- extract the .exe and put it in the same directory of the .db
"""

def setup_db():
    """Checks for the database, creates it if it doesn't exist, and returns the connection."""
    # Create the database and table if they don't exist
    conn = sqlite3.connect(f'{DB_NAME}.db')
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        season TEXT,
        status TEXT,
        last TEXT
        )
    ''')
    conn.commit()
    return conn

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If we are not running as a .exe, just look in the current folder
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AnimeTrackerApp:
    def __init__(self, root, conn):
        self.root = root
        self.conn = conn
        self.cursor = conn.cursor()
        
        # Configure Main Window
        self.root.title("Anime Tracker")
        self.root.geometry("750x450")
        icon_path = resource_path('ramen.ico')
        self.root.iconbitmap(icon_path)
        
        # --- UI Setup ---
        
        # Top Frame for Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, fill=tk.X, padx=10)
        
        # Clickable Action Buttons
        tk.Button(button_frame, text="Add New", width=12, command=self.add_window).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Show All", width=12, command=lambda: self.refresh_tree("all")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Show Finished", width=15, command=lambda: self.refresh_tree("finished")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Show On-going", width=15, command=lambda: self.refresh_tree("on going")).pack(side=tk.LEFT, padx=5)
        
        # Right aligned action buttons
        tk.Button(button_frame, text="Delete", width=10, bg="#ffcccc", command=self.delete_anime).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Update", width=10, bg="#ccffcc", command=self.update_window).pack(side=tk.RIGHT, padx=5)
        
        # Treeview (Table) for displaying data
        columns = ("ID", "Title", "Season", "Status", "Last Ep")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        # Format the columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
            
        self.tree.column("Title", width=250, anchor=tk.W) # Left-align the title for readability
        self.tree.column("ID", width=50)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Populate the table on startup
        self.refresh_tree("all")
        
    def refresh_tree(self, filter_type):
        """Refreshes the table data based on the selected filter."""
        # Clear current items in the table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Fetch data based on the filter
        if filter_type == "all":
            self.cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        else:
            self.cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE status = ?", (filter_type,))
            
        # Insert fetched rows into the table
        for row in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=row)

    def add_window(self):
        """Opens a pop-up window to add a new anime."""
        win = tk.Toplevel(self.root)
        win.title("Add New Anime")
        win.geometry("300x250")
        win.grab_set() # Locks focus on this pop-up
        
        tk.Label(win, text="Title:").pack(pady=2)
        title_entry = tk.Entry(win, width=30)
        title_entry.pack()
        
        tk.Label(win, text="Season:").pack(pady=2)
        season_entry = tk.Entry(win, width=30)
        season_entry.pack()
        
        tk.Label(win, text="Status:").pack(pady=2)
        status_combo = ttk.Combobox(win, values=["on going", "finished"], state="readonly")
        status_combo.set("on going")
        status_combo.pack()
        
        tk.Label(win, text="Last Episode:").pack(pady=2)
        ep_entry = tk.Entry(win, width=30)
        ep_entry.pack()
        
        def save():
            t = title_entry.get().strip()
            s = season_entry.get().strip()
            st = status_combo.get()
            # Auto-assign '#' if finished
            ep = '#' if st == 'finished' else ep_entry.get().strip() 
            
            if not t:
                messagebox.showerror("Error", "Title cannot be empty!")
                return
                
            try:
                self.cursor.execute(f"INSERT INTO {TABLE_NAME} (title, season, status, last) VALUES (?, ?, ?, ?)",
                                    (t, s, st, ep))
                self.conn.commit()
                self.refresh_tree("all")
                win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Anime already exists in the database!")
                
        tk.Button(win, text="Save Anime", command=save).pack(pady=15)

    def update_window(self):
        """Opens a pop-up to edit the currently selected anime."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an anime from the list to update!")
            return
            
        # Get the current values of the selected row
        item_values = self.tree.item(selected[0], 'values')
        anime_id = item_values[0]
        
        win = tk.Toplevel(self.root)
        win.title("Update Anime")
        win.geometry("300x250")
        win.grab_set()
        
        # Pre-fill entries with current data
        tk.Label(win, text="Title:").pack(pady=2)
        title_entry = tk.Entry(win, width=30)
        title_entry.insert(0, item_values[1])
        title_entry.pack()
        
        tk.Label(win, text="Season:").pack(pady=2)
        season_entry = tk.Entry(win, width=30)
        season_entry.insert(0, item_values[2])
        season_entry.pack()
        
        tk.Label(win, text="Status:").pack(pady=2)
        status_combo = ttk.Combobox(win, values=["on going", "finished"], state="readonly")
        status_combo.set(item_values[3])
        status_combo.pack()
        
        tk.Label(win, text="Last Episode:").pack(pady=2)
        ep_entry = tk.Entry(win, width=30)
        ep_entry.insert(0, item_values[4] if item_values[4] != '#' else '')
        ep_entry.pack()
        
        def save_update():
            t = title_entry.get().strip()
            s = season_entry.get().strip()
            st = status_combo.get()
            ep = '#' if st == 'finished' else ep_entry.get().strip()
            
            self.cursor.execute(f"UPDATE {TABLE_NAME} SET title=?, season=?, status=?, last=? WHERE id=?",
                                (t, s, st, ep, anime_id))
            self.conn.commit()
            self.refresh_tree("all")
            win.destroy()
            
        tk.Button(win, text="Save Changes", command=save_update).pack(pady=15)

    def delete_anime(self):
        """Deletes the currently selected anime from the database."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an anime to delete!")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this anime?"):
            item_values = self.tree.item(selected[0], 'values')
            anime_id = item_values[0]
            
            self.cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id=?", (anime_id,))
            self.conn.commit()
            self.refresh_tree("all")

if __name__ == '__main__':
    # Initialize the database
    conn = setup_db()
    
    # Start the Tkinter main loop
    root = tk.Tk()
    app = AnimeTrackerApp(root, conn)
    root.mainloop()
    
    # Close connection when the application window is closed
    conn.close()
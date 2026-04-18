"""
AniDex  –  Professional Anime Tracker
──────────────────────────────────────────────────────────────────────────────
Layout:   Left sidebar (nav + stats) │ Right content (header + search + table)
Theme:    Deep-space dark, crimson-gold accent, editorial typography
New UX:   Live search, toast notifications, animated status badges,
          sortable columns, hover-highlight rows, keyboard shortcuts,
          smooth modal dialogs, entry-count dashboard cards.
          Extra statuses: plan to watch, dropped.
"""

import sqlite3
import os
import sys
import tkinter as tk
from tkinter import ttk

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
DB_NAME    = "AnimeWatchList"
TABLE_NAME = "ANIME"

def setup_db():
    conn = sqlite3.connect(f"{DB_NAME}.db")
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            title  TEXT    NOT NULL,
            season TEXT    DEFAULT '',
            status TEXT    DEFAULT 'on going',
            last   TEXT    DEFAULT ''
        )""")
    conn.commit()
    return conn

def resource_path(rel):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, rel)

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE  &  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":          "#080b14",
    "sidebar":     "#0c1020",
    "surface":     "#111827",
    "surface2":    "#1a2235",
    "surface3":    "#222d42",
    "border":      "#1e2d47",
    "accent":      "#e8383d",
    "accent_dim":  "#7a1a1d",
    "gold":        "#d4af37",
    "gold_dim":    "#6b580e",
    "text":        "#e8eaf0",
    "text_mid":    "#8b95b0",
    "text_dim":    "#4a5568",
    "green":       "#10b981",
    "green_dim":   "#064e3b",
    "amber":       "#f59e0b",
    "amber_dim":   "#451a03",
    "blue":        "#3b82f6",
    "blue_dim":    "#1e3a5f",
    "red_soft":    "#ff6b6b",
    "white":       "#ffffff",
}

F = {
    "display":  ("Georgia",      20, "bold"),
    "title":    ("Georgia",      14, "bold"),
    "heading":  ("Courier New",   9, "bold"),
    "body":     ("Courier New",  10),
    "body_sm":  ("Courier New",   9),
    "mono":     ("Courier New",  10),
    "label":    ("Courier New",   8, "bold"),
    "badge":    ("Courier New",   8, "bold"),
    "nav":      ("Courier New",  10, "bold"),
    "btn":      ("Courier New",   9, "bold"),
    "btn_lg":   ("Courier New",  10, "bold"),
    "stat_num": ("Georgia",      22, "bold"),
    "stat_lbl": ("Courier New",   8),
}

ROW_H = 34

STATUS_ICONS = {
    "on going":      "▶",
    "finished":      "✓",
    "plan to watch": "○",
    "dropped":       "✕",
}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITY WIDGETS
# ─────────────────────────────────────────────────────────────────────────────
class HoverButton(tk.Label):
    """Flat label-button with hover colour swap."""
    def __init__(self, parent, text, command, bg, fg,
                 hover_bg=None, hover_fg=None, font=F["btn"],
                 padx=14, pady=7, **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font,
                         padx=padx, pady=pady, cursor="hand2", **kw)
        self._bg  = bg;  self._fg  = fg
        self._hbg = hover_bg or C["accent"]
        self._hfg = hover_fg or C["white"]
        self._cmd = command
        self.bind("<Enter>",           lambda _: self.configure(bg=self._hbg, fg=self._hfg))
        self.bind("<Leave>",           lambda _: self.configure(bg=self._bg,  fg=self._fg))
        self.bind("<ButtonRelease-1>", lambda _: self._cmd() if self._cmd else None)


class Divider(tk.Frame):
    def __init__(self, parent, color=None, **kw):
        super().__init__(parent, bg=color or C["border"], height=1, **kw)


class Toast:
    """Slide-in toast notification, auto-dismisses after 2.5 s."""
    _pool = []

    def __init__(self, root, message, kind="info"):
        Toast._pool = [t for t in Toast._pool if t.win.winfo_exists()]
        Toast._pool.append(self)
        self.win = w = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        palette = {
            "info":    (C["blue"],   C["blue_dim"]),
            "success": (C["green"],  C["green_dim"]),
            "error":   (C["accent"], C["accent_dim"]),
        }
        fg, bg = palette.get(kind, palette["info"])
        icons  = {"info": "ℹ", "success": "✓", "error": "✕"}
        w.configure(bg=bg)
        f = tk.Frame(w, bg=bg, padx=14, pady=10);  f.pack()
        tk.Label(f, text=icons.get(kind,"ℹ"), bg=bg, fg=fg,
                 font=("Courier New", 12, "bold")).pack(side=tk.LEFT, padx=(0,8))
        tk.Label(f, text=message, bg=bg, fg=C["text"],
                 font=F["body"]).pack(side=tk.LEFT)
        w.update_idletasks()
        pw, ph = w.winfo_reqwidth(), w.winfo_reqheight()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        stack_off = sum(
            t.win.winfo_reqheight() + 6
            for t in Toast._pool[:-1] if t.win.winfo_exists()
        )
        w.geometry(f"{pw}x{ph}+{sw-pw-20}+{sh-ph-stack_off-70}")
        w.after(2500, self._close)

    def _close(self):
        if self.win.winfo_exists():
            self.win.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# CANVAS GRADIENT HEADER
# ─────────────────────────────────────────────────────────────────────────────
class GradientHeader(tk.Canvas):
    def __init__(self, parent, h=68, **kw):
        super().__init__(parent, height=h, bd=0, highlightthickness=0, **kw)
        self._h = h
        self.bind("<Configure>", self._draw)

    def _draw(self, _=None):
        self.delete("all")
        w, h = self.winfo_width() or 800, self._h
        steps = 28
        for i in range(steps):
            r = int(0x08 + (0x16 - 0x08) * i / steps)
            g = int(0x0b + (0x1c - 0x0b) * i / steps)
            b = int(0x14 + (0x2e - 0x14) * i / steps)
            self.create_rectangle(0, h*i//steps, w, h*(i+1)//steps+1,
                                  fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        # accent stripe
        self.create_rectangle(0, h-3, w, h, fill=C["accent"], outline="")
        # faint grid
        for x in range(0, w, 48):
            self.create_line(x, 0, x, h, fill="#ffffff07")
        # title
        self.create_text(20, h//2, text="ANIDEX", anchor="w",
                         fill=C["text"], font=("Georgia", 18, "bold"))
        self.create_text(112, h//2+2, text="TRACKER", anchor="w",
                         fill=C["accent"], font=("Courier New", 9, "bold"))
        # deco
        self.create_text(w-16, 14, text="ア ニ メ", anchor="e",
                         fill=C["text_dim"], font=("Courier New", 9))


# ─────────────────────────────────────────────────────────────────────────────
# MODAL DIALOG  (Add / Edit)
# ─────────────────────────────────────────────────────────────────────────────
class AnimeDialog(tk.Toplevel):
    def __init__(self, parent, title, on_save, defaults=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.on_save = on_save
        d = defaults or {}

        W, H = 380, 430
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - W // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - H // 2
        self.geometry(f"{W}x{H}+{px}+{py}")

        # accent bar
        tk.Frame(self, bg=C["accent"], height=3).pack(fill=tk.X)
        # title row
        top = tk.Frame(self, bg=C["surface"], pady=14);  top.pack(fill=tk.X)
        tk.Label(top, text=title.upper(), bg=C["surface"],
                 fg=C["text"], font=F["title"]).pack(side=tk.LEFT, padx=20)
        Divider(self).pack(fill=tk.X)

        # body
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=12)
        body.columnconfigure(0, weight=1)

        def lbl(text, row):
            tk.Label(body, text=text, bg=C["bg"], fg=C["text_mid"],
                     font=F["label"], anchor="w").grid(
                         row=row, column=0, sticky="w", pady=(10, 2))

        def entry_w(row, default=""):
            e = tk.Entry(body, bg=C["surface2"], fg=C["text"],
                         insertbackground=C["accent"], relief="flat",
                         font=F["mono"], highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["accent"])
            e.insert(0, default)
            e.grid(row=row, column=0, sticky="ew", ipady=7)
            return e

        lbl("TITLE *",        0);  self.e_title  = entry_w(1, d.get("title",  ""))
        lbl("SEASON",         2);  self.e_season = entry_w(3, d.get("season", ""))
        lbl("STATUS",         4)

        STATUS_OPTS = ["on going", "finished", "plan to watch", "dropped"]
        self.sv = tk.StringVar(value=d.get("status", "on going"))
        # tk.OptionMenu is fully styleable — no system-color overrides
        om = tk.OptionMenu(body, self.sv, *STATUS_OPTS)
        om.configure(
            bg=C["surface2"], fg=C["text"], font=F["mono"],
            activebackground=C["accent"], activeforeground=C["white"],
            highlightthickness=1, highlightbackground=C["border"],
            highlightcolor=C["accent"],
            relief="flat", cursor="hand2", anchor="w",
            indicatoron=True, bd=0)
        # Style the dropdown list itself
        om["menu"].configure(
            bg=C["surface2"], fg=C["text"], font=F["mono"],
            activebackground=C["accent"], activeforeground=C["white"],
            borderwidth=0, relief="flat")
        om.grid(row=5, column=0, sticky="ew", ipady=6)
        self.sv.trace_add("write", self._status_changed)

        lbl("LAST EPISODE",   6);  self.e_ep = entry_w(7, d.get("last", ""))
        self._status_changed()

        # buttons
        Divider(self).pack(fill=tk.X)
        br = tk.Frame(self, bg=C["surface"], pady=12);  br.pack(fill=tk.X)
        HoverButton(br, "CANCEL", self.destroy, bg=C["surface3"],
                    fg=C["text_mid"], hover_bg=C["surface2"],
                    hover_fg=C["text"], font=F["btn_lg"]).pack(
                        side=tk.LEFT, padx=(20, 6))
        HoverButton(br, "  SAVE  ", self._save, bg=C["accent"],
                    fg=C["white"], hover_bg="#ff5055",
                    hover_fg=C["white"], font=F["btn_lg"]).pack(
                        side=tk.RIGHT, padx=(6, 20))

        self.e_title.focus_set()
        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _status_changed(self, *_):
        closed = self.sv.get() in ("finished", "dropped")
        self.e_ep.configure(
            state="disabled" if closed else "normal",
            bg=C["surface3"]  if closed else C["surface2"])

    def _save(self):
        t  = self.e_title.get().strip()
        s  = self.e_season.get().strip()
        st = self.sv.get()
        ep = "—" if st in ("finished", "dropped") else self.e_ep.get().strip()
        if not t:
            Toast(self.master, "Title cannot be empty!", "error")
            self.e_title.focus_set()
            return
        self.on_save(t, s, st, ep)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRM DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent, message, on_confirm):
        super().__init__(parent)
        self.configure(bg=C["surface"])
        self.resizable(False, False)
        self.grab_set()
        self.title("Confirm")
        W, H = 320, 155
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - W // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - H // 2
        self.geometry(f"{W}x{H}+{px}+{py}")
        tk.Frame(self, bg=C["accent"], height=3).pack(fill=tk.X)
        tk.Label(self, text=message, bg=C["surface"], fg=C["text"],
                 font=F["body"], wraplength=280,
                 justify="center").pack(pady=22)
        row = tk.Frame(self, bg=C["surface"]);  row.pack()
        HoverButton(row, "CANCEL", self.destroy, bg=C["surface3"],
                    fg=C["text_mid"], hover_bg=C["surface2"],
                    hover_fg=C["text"]).pack(side=tk.LEFT, padx=8)
        HoverButton(row, "DELETE", lambda: [on_confirm(), self.destroy()],
                    bg=C["accent_dim"], fg=C["red_soft"],
                    hover_bg=C["accent"], hover_fg=C["white"]).pack(
                        side=tk.LEFT, padx=8)
        self.bind("<Escape>", lambda _: self.destroy())


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class AniDexApp:
    def __init__(self, root, conn):
        self.root   = root
        self.conn   = conn
        self.cur    = conn.cursor()
        self._filter   = "all"
        self._search_q = ""
        self._sort_col = None
        self._sort_asc = True
        self._hovered  = None

        self._configure_root()
        self._build_styles()
        self._build_sidebar()
        self._build_content()
        self._bind_keys()
        self.refresh()

    # ── Root ──────────────────────────────────────────────────────────────────
    def _configure_root(self):
        self.root.title("AniDex")
        self.root.geometry("1020x620")
        self.root.minsize(800, 480)
        self.root.configure(bg=C["bg"])
        ico = resource_path("ramen.ico")
        if os.path.exists(ico):
            self.root.iconbitmap(ico)

    # ── ttk Styles ────────────────────────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style();  s.theme_use("clam")
        s.configure("AniDex.Treeview",
                     background=C["surface"], foreground=C["text"],
                     fieldbackground=C["surface"], rowheight=ROW_H,
                     font=F["body"], borderwidth=0, relief="flat")
        s.configure("AniDex.Treeview.Heading",
                     background=C["surface2"], foreground=C["text_mid"],
                     font=F["heading"], relief="flat", padding=(8, 8))
        s.map("AniDex.Treeview",
              background=[("selected", C["surface3"])],
              foreground=[("selected", C["text"])])
        s.map("AniDex.Treeview.Heading",
              background=[("active", C["surface3"])])
        s.configure("Slim.Vertical.TScrollbar",
                     background=C["surface2"], troughcolor=C["bg"],
                     arrowcolor=C["text_dim"], borderwidth=0,
                     relief="flat", width=10)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self.root, bg=C["sidebar"], width=210)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        # Logo
        tk.Label(sb, text="彡", bg=C["sidebar"],
                 fg=C["accent"], font=("Georgia", 28)).pack(pady=(22, 2))
        tk.Label(sb, text="AniDex", bg=C["sidebar"],
                 fg=C["text"], font=F["title"]).pack()
        tk.Label(sb, text="anime tracker", bg=C["sidebar"],
                 fg=C["text_dim"], font=F["body_sm"]).pack(pady=(0, 16))

        Divider(sb).pack(fill=tk.X, padx=16)

        # ── Stat cards ────────────────────────────────────────────────────
        self._cards = {}
        stats = [
            ("total",         "TOTAL",         C["gold"]),
            ("on going",      "ON-GOING",       C["amber"]),
            ("finished",      "FINISHED",       C["green"]),
            ("plan to watch", "PLAN TO WATCH",  C["blue"]),
            ("dropped",       "DROPPED",        C["text_mid"]),
        ]
        for key, label, color in stats:
            card = tk.Frame(sb, bg=C["sidebar"])
            card.pack(fill=tk.X, padx=12, pady=3)
            tk.Frame(card, bg=color, width=3).pack(side=tk.LEFT, fill=tk.Y)
            inner = tk.Frame(card, bg=C["surface2"])
            inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))
            nv = tk.StringVar(value="0")
            tk.Label(inner, textvariable=nv, bg=C["surface2"],
                     fg=color, font=("Georgia", 16, "bold")).pack(
                         side=tk.LEFT, padx=(8, 4), pady=6)
            tk.Label(inner, text=label, bg=C["surface2"],
                     fg=C["text_dim"], font=F["label"]).pack(side=tk.LEFT)
            self._cards[key] = nv

        Divider(sb).pack(fill=tk.X, padx=16, pady=10)

        # ── Nav ───────────────────────────────────────────────────────────
        tk.Label(sb, text="FILTER BY STATUS", bg=C["sidebar"],
                 fg=C["text_dim"], font=F["label"]).pack(
                     anchor="w", padx=16, pady=(0, 4))

        self._nav_btns = {}
        nav = [
            ("ALL",           "all"),
            ("ON-GOING",      "on going"),
            ("FINISHED",      "finished"),
            ("PLAN TO WATCH", "plan to watch"),
            ("DROPPED",       "dropped"),
        ]
        for label, key in nav:
            b = tk.Label(sb, text=f"  {label}", bg=C["sidebar"],
                         fg=C["text_mid"], font=F["nav"],
                         anchor="w", cursor="hand2", padx=8, pady=7)
            b.pack(fill=tk.X, padx=8)
            b.bind("<Enter>",  lambda e, w=b: w.configure(
                bg=C["surface3"], fg=C["text"]))
            b.bind("<Leave>",  lambda e, w=b, k=key: w.configure(
                bg=C["accent_dim"] if self._filter == k else C["sidebar"],
                fg=C["text"]       if self._filter == k else C["text_mid"]))
            b.bind("<ButtonRelease-1>", lambda e, k=key: self._set_filter(k))
            self._nav_btns[key] = b

        tk.Label(sb, text="v2.0  ·  AniDex", bg=C["sidebar"],
                 fg=C["text_dim"], font=F["label"]).pack(
                     side=tk.BOTTOM, pady=12)

    # ── Content pane ─────────────────────────────────────────────────────────
    def _build_content(self):
        pane = tk.Frame(self.root, bg=C["bg"])
        pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Canvas header
        GradientHeader(pane, bg=C["bg"]).pack(fill=tk.X)

        # ── Toolbar ───────────────────────────────────────────────────────
        tb = tk.Frame(pane, bg=C["surface"]);  tb.pack(fill=tk.X)

        # Search
        sw = tk.Frame(tb, bg=C["surface2"],
                      highlightthickness=1, highlightbackground=C["border"],
                      highlightcolor=C["accent"])
        sw.pack(side=tk.LEFT, padx=14, pady=10)
        tk.Label(sw, text="⌕", bg=C["surface2"], fg=C["text_mid"],
                 font=("Courier New", 13)).pack(side=tk.LEFT, padx=(8, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        tk.Entry(sw, textvariable=self.search_var, bg=C["surface2"],
                 fg=C["text"], insertbackground=C["accent"],
                 relief="flat", font=F["mono"], width=26,
                 highlightthickness=0).pack(side=tk.LEFT, ipady=7, padx=(0, 8))
        tk.Label(sw, text="SEARCH", bg=C["surface2"],
                 fg=C["text_dim"], font=F["label"]).pack(side=tk.LEFT, padx=(0, 8))

        # Buttons
        HoverButton(tb, "＋  ADD",    self._add,
                    bg=C["accent"],   fg=C["white"],
                    hover_bg="#ff5055", font=F["btn_lg"]
                    ).pack(side=tk.RIGHT, padx=(4, 14), pady=8)
        HoverButton(tb, "✎  EDIT",   self._edit,
                    bg=C["surface2"], fg=C["text_mid"],
                    hover_bg=C["surface3"], hover_fg=C["text"],
                    font=F["btn_lg"]
                    ).pack(side=tk.RIGHT, padx=4, pady=8)
        HoverButton(tb, "✕  DELETE", self._delete,
                    bg=C["surface2"], fg=C["text_mid"],
                    hover_bg=C["accent_dim"], hover_fg=C["red_soft"],
                    font=F["btn_lg"]
                    ).pack(side=tk.RIGHT, padx=4, pady=8)

        Divider(pane).pack(fill=tk.X)

        # ── Table ─────────────────────────────────────────────────────────
        tf = tk.Frame(pane, bg=C["bg"]);  tf.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Title", "Season", "Status", "Last Ep")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings",
                                  style="AniDex.Treeview", selectmode="browse")

        widths  = {"ID": 46, "Title": 300, "Season": 120,
                   "Status": 140, "Last Ep": 90}
        anchors = {"ID": tk.CENTER, "Title": tk.W,
                   "Season": tk.CENTER, "Status": tk.CENTER, "Last Ep": tk.CENTER}

        for col in cols:
            self.tree.heading(col, text=f"  {col}",
                              command=lambda c=col: self._sort(c))
            self.tree.column(col, width=widths[col],
                             anchor=anchors[col], stretch=(col == "Title"))

        # Row tags
        self.tree.tag_configure("odd",     background=C["surface"])
        self.tree.tag_configure("even",    background=C["bg"])
        self.tree.tag_configure("hover",   background=C["surface3"])
        self.tree.tag_configure("ongoing", foreground=C["amber"])
        self.tree.tag_configure("done",    foreground=C["green"])
        self.tree.tag_configure("plan",    foreground=C["blue"])
        self.tree.tag_configure("drop",    foreground=C["text_mid"])

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview,
                             style="Slim.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Motion>",           self._on_hover)
        self.tree.bind("<Leave>",            self._on_leave)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         lambda _: self._edit())

        # ── Status bar ────────────────────────────────────────────────────
        Divider(pane).pack(fill=tk.X)
        sb2 = tk.Frame(pane, bg=C["surface"], pady=5);  sb2.pack(fill=tk.X)
        self.status_var = tk.StringVar(value="Ready.")
        self.sel_var    = tk.StringVar(value="")
        tk.Label(sb2, textvariable=self.status_var, bg=C["surface"],
                 fg=C["text_dim"], font=F["body_sm"]).pack(
                     side=tk.LEFT, padx=14)
        tk.Label(sb2, text="Ctrl+N  Add  ·  Ctrl+E  Edit  ·  Del  Delete  ·  F5  Refresh",
                 bg=C["surface"], fg=C["text_dim"],
                 font=F["body_sm"]).pack(side=tk.RIGHT, padx=14)

    # ── Key bindings ─────────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<Control-n>", lambda _: self._add())
        self.root.bind("<Control-e>", lambda _: self._edit())
        self.root.bind("<Delete>",    lambda _: self._delete())
        self.root.bind("<F5>",        lambda _: self.refresh())

    # ── Hover ─────────────────────────────────────────────────────────────────
    def _on_hover(self, event):
        item = self.tree.identify_row(event.y)
        if item == self._hovered:
            return
        if self._hovered and self.tree.exists(self._hovered):
            tags = [t for t in self.tree.item(self._hovered, "tags") if t != "hover"]
            self.tree.item(self._hovered, tags=tags)
        if item:
            tags = list(self.tree.item(item, "tags")) + ["hover"]
            self.tree.item(item, tags=tags)
        self._hovered = item

    def _on_leave(self, _=None):
        if self._hovered and self.tree.exists(self._hovered):
            tags = [t for t in self.tree.item(self._hovered, "tags") if t != "hover"]
            self.tree.item(self._hovered, tags=tags)
        self._hovered = None

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            v = self.tree.item(sel[0], "values")
            self.status_var.set(f"Selected: {v[1]}")

    # ── Filter / search ───────────────────────────────────────────────────────
    def _set_filter(self, key):
        self._filter = key
        self._update_nav()
        self.refresh()

    def _update_nav(self):
        for key, btn in self._nav_btns.items():
            active = key == self._filter
            btn.configure(
                bg=C["accent_dim"] if active else C["sidebar"],
                fg=C["text"]       if active else C["text_mid"])

    def _on_search(self, *_):
        self._search_q = self.search_var.get().strip().lower()
        self.refresh()

    # ── Sort ─────────────────────────────────────────────────────────────────
    def _sort(self, col):
        self._sort_asc = not self._sort_asc if self._sort_col == col else True
        self._sort_col = col
        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self._filter == "all":
            self.cur.execute(f"SELECT * FROM {TABLE_NAME}")
        else:
            self.cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE status=?",
                             (self._filter,))
        rows = self.cur.fetchall()

        # Search
        q = self._search_q
        if q:
            rows = [r for r in rows if
                    q in r[1].lower() or
                    q in (r[2] or "").lower() or
                    q in r[3].lower()]

        # Sort
        idx_map = {"ID": 0, "Title": 1, "Season": 2, "Status": 3, "Last Ep": 4}
        if self._sort_col and self._sort_col in idx_map:
            idx = idx_map[self._sort_col]
            try:
                rows = sorted(rows, key=lambda r: int(r[idx] or 0),
                              reverse=not self._sort_asc)
            except (ValueError, TypeError):
                rows = sorted(rows, key=lambda r: (r[idx] or "").lower(),
                              reverse=not self._sort_asc)

        # Insert rows
        tag_map = {
            "on going":      "ongoing",
            "finished":      "done",
            "plan to watch": "plan",
            "dropped":       "drop",
        }
        for i, row in enumerate(rows):
            parity = "odd" if i % 2 else "even"
            st     = row[3]
            st_tag = tag_map.get(st, "ongoing")
            icon   = STATUS_ICONS.get(st, "")
            disp   = list(row)
            disp[3] = f"{icon}  {st}"
            self.tree.insert("", tk.END, values=disp, tags=(parity, st_tag))

        # Stat cards
        self.cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        self._cards["total"].set(self.cur.fetchone()[0])
        for status in ("on going", "finished", "plan to watch", "dropped"):
            self.cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE status=?",
                             (status,))
            self._cards[status].set(self.cur.fetchone()[0])

        n = len(rows)
        desc = f"{n} entr{'y' if n==1 else 'ies'}"
        if self._filter != "all": desc += f"  ·  {self._filter}"
        if self._search_q:        desc += f"  ·  '{self._search_q}'"
        self.status_var.set(desc)
        self._update_nav()

    # ── CRUD actions ─────────────────────────────────────────────────────────
    def _add(self):
        def on_save(t, s, st, ep):
            try:
                self.cur.execute(
                    f"INSERT INTO {TABLE_NAME} (title,season,status,last)"
                    f" VALUES (?,?,?,?)", (t, s, st, ep))
                self.conn.commit()
                self.refresh()
                Toast(self.root, f'Added "{t}"', "success")
            except Exception as ex:
                Toast(self.root, str(ex), "error")
        AnimeDialog(self.root, "Add New Anime", on_save)

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            Toast(self.root, "Select an anime to edit.", "info");  return
        vals     = self.tree.item(sel[0], "values")
        anime_id = vals[0]
        raw_st   = vals[3].split("  ", 1)[-1] if "  " in vals[3] else vals[3]
        raw_ep   = "" if vals[4] == "—" else vals[4]
        defaults = {"title": vals[1], "season": vals[2],
                    "status": raw_st, "last": raw_ep}

        def on_save(t, s, st, ep):
            self.cur.execute(
                f"UPDATE {TABLE_NAME} SET title=?,season=?,status=?,last=?"
                f" WHERE id=?", (t, s, st, ep, anime_id))
            self.conn.commit()
            self.refresh()
            Toast(self.root, f'Updated "{t}"', "success")
        AnimeDialog(self.root, "Edit Anime", on_save, defaults)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            Toast(self.root, "Select an anime to delete.", "info");  return
        vals  = self.tree.item(sel[0], "values")
        title = vals[1]
        aid   = vals[0]

        def confirmed():
            self.cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id=?", (aid,))
            self.conn.commit()
            self.refresh()
            Toast(self.root, f'Deleted "{title}"', "error")
        ConfirmDialog(self.root, f'Delete "{title}"?', confirmed)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    conn = setup_db()
    root = tk.Tk()
    AniDexApp(root, conn)
    root.mainloop()
    conn.close()
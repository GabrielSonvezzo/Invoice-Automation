# =============================================================================
# gui.py — Main Interface
# Invoice Management System
# Version 2.0 Pro — Dashboard | Processing | Settings | Logs | Backups
# =============================================================================

import customtkinter as ctk
import threading
import os
import sys
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

# ── System Imports ──
try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

import database
import config
import backup

try:
    from invoice_bot import process_files
except ImportError:
    def process_files(callback=None):
        if callback: callback("❌ Error: invoice_bot.py not found.")


def resource_path(relative_path):
    """ Returns the absolute path to resources, working inside and outside PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════
BLUE        = "#1A6FD4"
BLUE_HOVER  = "#1558AF"
GREEN       = "#22C55E"
RED         = "#EF4444"
YELLOW      = "#F59E0B"
CARD_GRAY   = "#1E2130"
BG_GRAY     = "#141520"
BORDER_GRAY = "#2A2D3E"
WHITE       = "#F0F4FF"
TEXT_MUTED  = "#8B92A9"


# ══════════════════════════════════════════════════════════════════════════════
#  REUSABLE KPI CARD
# ══════════════════════════════════════════════════════════════════════════════
class CardKPI(ctk.CTkFrame):
    def __init__(self, master, title, value, icon, icon_color=BLUE, **kwargs):
        super().__init__(master, fg_color=CARD_GRAY, corner_radius=12,
                         border_width=1, border_color=BORDER_GRAY, **kwargs)

        ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 22),
                     text_color=icon_color).pack(pady=(14, 0))
        self.lbl_value = ctk.CTkLabel(self, text=str(value),
                                      font=("Segoe UI", 26, "bold"),
                                      text_color=WHITE)
        self.lbl_value.pack()
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 11),
                     text_color=TEXT_MUTED).pack(pady=(2, 14))

    def update_value(self, value):
        self.lbl_value.configure(text=str(value))


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP CLASS
# ══════════════════════════════════════════════════════════════════════════════
class InvoiceSystemApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        database.initialize()

        self.title("Invoice System Pro")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=BG_GRAY)

        self._processing = False
        self._cfg = config.load()

        self._build_layout()
        self._tab_dashboard()
        self.after(200, self._update_dashboard)

    # ─────────────────────────────────────────────────────────────────────────
    #  BASE LAYOUT
    # ─────────────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=CARD_GRAY,
                                    corner_radius=0, border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        self._logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._logo_frame.pack(pady=(20, 10), padx=10)

        if PIL_OK:
            logo_path = resource_path("logo.png")
            
            if os.path.exists(logo_path):
                try:
                    img = Image.open(logo_path)
                    w, h = img.size
                    nw = 160
                    nh = int(h * nw / w)
                    self._img_logo = ctk.CTkImage(light_image=img, dark_image=img, size=(nw, nh))
                    ctk.CTkLabel(self._logo_frame, image=self._img_logo, text="").pack()
                except Exception:
                    pass
                
        ctk.CTkLabel(self.sidebar, text="INVOICES", font=("Segoe UI", 12, "bold"),
                     text_color=BLUE).pack(pady=(0, 4))
        ctk.CTkLabel(self.sidebar, text="Admin Panel", font=("Segoe UI", 10),
                     text_color=TEXT_MUTED).pack(pady=(0, 20))

        # Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_GRAY).pack(fill="x", padx=15, pady=4)

        # Navigation Buttons
        self._current_btn = None
        self._nav_buttons = {}

        tabs = [
            ("📊  Dashboard",      "dashboard"),
            ("🚀  Process Invoices", "processing"),
            ("⚙️   Settings",       "settings"),
            ("📋  Audit Log",        "log"),
            ("💾  Backups",          "backups"),
            ("📧  Outlook (Soon)",   "outlook"),
        ]
        for text, key in tabs:
            btn = ctk.CTkButton(
                self.sidebar, text=text, anchor="w",
                font=("Segoe UI", 13), height=42,
                fg_color="transparent", hover_color="#252840",
                text_color=WHITE, corner_radius=8,
                command=lambda k=key: self._navigate(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

        # Content Area
        self.area = ctk.CTkFrame(self, fg_color=BG_GRAY, corner_radius=0)
        self.area.pack(side="left", fill="both", expand=True)

    def _navigate(self, key):
        # Deselect previous
        if self._current_btn:
            self._current_btn.configure(fg_color="transparent")
        btn = self._nav_buttons.get(key)
        if btn:
            btn.configure(fg_color=BLUE)
            self._current_btn = btn

        # Clear area
        for w in self.area.winfo_children():
            w.destroy()

        method = getattr(self, f"_tab_{key}", None)
        if method:
            method()

    # ─────────────────────────────────────────────────────────────────────────
    #  DASHBOARD TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_dashboard(self):
        self._navigate_no_reset("dashboard")
        f = self.area

        ctk.CTkLabel(f, text="Dashboard", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))
        ctk.CTkLabel(f, text="Invoices Overview", font=("Segoe UI", 13),
                     text_color=TEXT_MUTED).pack(anchor="w", padx=30)

        # KPI Cards
        row_cards = ctk.CTkFrame(f, fg_color="transparent")
        row_cards.pack(fill="x", padx=30, pady=20)

        self._card_invs   = CardKPI(row_cards, "Total Received", "—", "📄", BLUE)
        self._card_value  = CardKPI(row_cards, "Total Value (R$)", "—", "💰", GREEN)
        self._card_bkp    = CardKPI(row_cards, "Saved Backups", "—", "💾", YELLOW)
        self._card_anom   = CardKPI(row_cards, "Pending Alerts", "—", "⚠️", RED)

        for card in [self._card_invs, self._card_value, self._card_bkp, self._card_anom]:
            card.pack(side="left", expand=True, fill="both", padx=6)

        # Latest Invoices Table
        ctk.CTkLabel(f, text="Latest Processed Invoices", font=("Segoe UI", 15, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(10, 6))

        table_frame = ctk.CTkFrame(f, fg_color=CARD_GRAY, corner_radius=12,
                                   border_width=1, border_color=BORDER_GRAY)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Header
        header = ctk.CTkFrame(table_frame, fg_color="#252840", corner_radius=8)
        header.pack(fill="x", padx=10, pady=(10, 0))

        columns = [("Invoice", 80), ("Supplier", 110), ("Value (R$)", 130),
                   ("Inv Date", 100), ("Batch", 100), ("Processed At", 180)]
        for txt, w in columns:
            ctk.CTkLabel(header, text=txt, font=("Segoe UI", 11, "bold"),
                         text_color=TEXT_MUTED, width=w, anchor="w").pack(side="left", padx=8, pady=6)

        # Data Rows
        self._frame_rows_dash = ctk.CTkScrollableFrame(table_frame, fg_color="transparent",
                                                       height=200)
        self._frame_rows_dash.pack(fill="both", expand=True, padx=10, pady=4)

        self._update_dashboard()

    def _update_dashboard(self):
        try:
            total_invs  = database.total_invoices_month()
            total_value = database.total_value_month()
            bkps        = database.list_backups()
            alerts      = database.pending_alerts()

            if hasattr(self, "_card_invs"):
                self._card_invs.update_value(total_invs)
                self._card_value.update_value(f"R$ {total_value:,.2f}")
                self._card_bkp.update_value(len(bkps))
                self._card_anom.update_value(len(alerts))

            if hasattr(self, "_frame_rows_dash"):
                for w in self._frame_rows_dash.winfo_children():
                    w.destroy()

                invoices = database.list_invoices(15)
                for i, inv in enumerate(invoices):
                    bg = "#1A1D2E" if i % 2 == 0 else "transparent"
                    row = ctk.CTkFrame(self._frame_rows_dash, fg_color=bg, corner_radius=4)
                    row.pack(fill="x", pady=1)

                    row_data = [
                        (inv.get("invoice_num", ""), 80),
                        (str(inv.get("supplier", "")), 110),
                        (f"R$ {float(inv.get('total_value', 0)):,.2f}", 130),
                        (inv.get("inv_date", ""), 100),
                        (inv.get("batch", ""), 100),
                        (inv.get("processed_date", ""), 180),
                    ]
                    for txt, w in row_data:
                        ctk.CTkLabel(row, text=str(txt)[:25], font=("Segoe UI", 11),
                                     text_color=WHITE, width=w, anchor="w").pack(side="left", padx=8, pady=4)
        except Exception:
            pass

    def _navigate_no_reset(self, key):
        """Highlights button without clearing area (used on startup)."""
        if self._current_btn:
            self._current_btn.configure(fg_color="transparent")
        btn = self._nav_buttons.get(key)
        if btn:
            btn.configure(fg_color=BLUE)
            self._current_btn = btn

    # ─────────────────────────────────────────────────────────────────────────
    #  PROCESSING TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_processing(self):
        f = self.area
        cfg = config.load()

        ctk.CTkLabel(f, text="Process Invoices", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))
        ctk.CTkLabel(f, text="Reads pending XMLs and automatically logs them in the spreadsheet",
                     font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", padx=30)

        # Configured folders info
        info_frame = ctk.CTkFrame(f, fg_color=CARD_GRAY, corner_radius=12,
                                  border_width=1, border_color=BORDER_GRAY)
        info_frame.pack(fill="x", padx=30, pady=20)

        xml_folder = cfg.get("xml_folder", "Not configured")
        excel_path = cfg.get("excel_file", "Not configured")

        for label, value in [("📂 XML Folder:", xml_folder), ("📊 Spreadsheet:", excel_path)]:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 12, "bold"),
                         text_color=TEXT_MUTED, width=120).pack(side="left")
            ctk.CTkLabel(row, text=value[:70] + ("..." if len(value) > 70 else ""),
                         font=("Segoe UI", 12), text_color=WHITE).pack(side="left")

        # Status
        self._lbl_status_proc = ctk.CTkLabel(f, text="Status: Ready to start",
                                              font=("Segoe UI", 13, "italic"),
                                              text_color=TEXT_MUTED)
        self._lbl_status_proc.pack(pady=(0, 6))

        # Progress bar
        self._bar_proc = ctk.CTkProgressBar(f, width=600, height=10, mode="determinate",
                                            progress_color=BLUE)
        self._bar_proc.set(0)
        self._bar_proc.pack(pady=4)

        # Execution log
        self._log_proc = ctk.CTkTextbox(f, width=700, height=250, font=("Consolas", 12),
                                         corner_radius=10, border_width=1,
                                         border_color=BORDER_GRAY,
                                         fg_color=CARD_GRAY, text_color=WHITE)
        self._log_proc.pack(pady=10, padx=30, fill="both", expand=True)

        # Buttons
        row_btns = ctk.CTkFrame(f, fg_color="transparent")
        row_btns.pack(pady=10)

        self._btn_process = ctk.CTkButton(
            row_btns, text="🚀  PROCESS INVOICES IN SPREADSHEET",
            command=self._start_processing,
            fg_color=BLUE, hover_color=BLUE_HOVER,
            font=("Segoe UI", 15, "bold"), height=48, width=380,
            corner_radius=10
        )
        self._btn_process.pack(side="left", padx=6)

        ctk.CTkButton(
            row_btns, text="🗑  Clear Log",
            command=lambda: self._log_proc.delete("1.0", "end"),
            fg_color="#2A2D3E", hover_color="#353850",
            font=("Segoe UI", 13), height=48, width=140, corner_radius=10
        ).pack(side="left", padx=6)

    def _write_log_proc(self, msg: str):
        if hasattr(self, "_log_proc"):
            self._log_proc.insert("end", f"{msg}\n")
            self._log_proc.see("end")

    def _start_processing(self):
        if self._processing:
            return
        self._processing = True

        cfg = config.load()
        if not cfg.get("xml_folder") or not cfg.get("excel_file"):
            messagebox.showwarning("Incomplete configuration",
                                   "Configure the XML folder and Excel file before processing.\n\nGo to ⚙️ Settings.")
            self._processing = False
            return

        self._btn_process.configure(state="disabled", text="⏳  PROCESSING...")
        self._log_proc.delete("1.0", "end")
        self._bar_proc.configure(mode="indeterminate")
        self._bar_proc.start()
        self._lbl_status_proc.configure(text="Status: Reading XMLs and matching batches...", text_color=YELLOW)

        threading.Thread(target=self._run_processing, daemon=True).start()

    def _run_processing(self):
        try:
            process_files(callback=self._write_log_proc)
            self.after(0, lambda: self._lbl_status_proc.configure(
                text="Status: ✅ Completed!", text_color=GREEN))
            self.after(0, lambda: self._bar_proc.set(1))
            self.after(500, self._update_dashboard)
        except Exception as e:
            self.after(0, lambda: self._write_log_proc(f"\n❌ CRITICAL ERROR: {e}"))
            self.after(0, lambda: self._lbl_status_proc.configure(
                text="Status: Error detected", text_color=RED))
        finally:
            self.after(0, lambda: self._bar_proc.stop())
            self.after(0, lambda: self._bar_proc.configure(mode="determinate"))
            self.after(0, lambda: self._btn_process.configure(
                state="normal", text="🚀  PROCESS INVOICES IN SPREADSHEET"))
            self._processing = False

    # ─────────────────────────────────────────────────────────────────────────
    #  SETTINGS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_settings(self):
        f = self.area
        cfg = config.load()

        ctk.CTkLabel(f, text="Settings", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))
        ctk.CTkLabel(f, text="Configure system paths and parameters",
                     font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=0)

        # ── Section: Paths ──
        self._section(scroll, "📂 File Paths")

        self._input_cfg_xml  = self._folder_field(scroll, "Pending XMLs Folder",
                                                  cfg.get("xml_folder", ""))
        self._input_cfg_proc = self._folder_field(scroll, "Processed XMLs Folder",
                                                  cfg.get("processed_folder", ""))
        self._input_cfg_excel= self._file_field(scroll, "Excel Spreadsheet (.xlsx)",
                                                cfg.get("excel_file", ""))

        # ── Section: Spreadsheet ──
        self._section(scroll, "📊 Spreadsheet Settings")

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=4)

        ctk.CTkLabel(row1, text="Sheet Name:", font=("Segoe UI", 12),
                     text_color=WHITE, width=180).pack(side="left")
        self._input_sheet = ctk.CTkEntry(row1, width=200, font=("Segoe UI", 12),
                                         fg_color=CARD_GRAY, border_color=BORDER_GRAY,
                                         text_color=WHITE)
        self._input_sheet.insert(0, cfg.get("sheet_name", "Steel Plant"))
        self._input_sheet.pack(side="left", padx=8)

        ctk.CTkLabel(row1, text="Batch Column:", font=("Segoe UI", 12),
                     text_color=WHITE, width=140).pack(side="left", padx=(20, 0))
        self._input_batch = ctk.CTkEntry(row1, width=60, font=("Segoe UI", 12),
                                         fg_color=CARD_GRAY, border_color=BORDER_GRAY,
                                         text_color=WHITE)
        self._input_batch.insert(0, cfg.get("batch_column", "W"))
        self._input_batch.pack(side="left", padx=8)

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Default Supplier:", font=("Segoe UI", 12),
                     text_color=WHITE, width=180).pack(side="left")
        self._input_supplier = ctk.CTkEntry(row2, width=120, font=("Segoe UI", 12),
                                            fg_color=CARD_GRAY, border_color=BORDER_GRAY,
                                            text_color=WHITE)
        self._input_supplier.insert(0, str(cfg.get("default_supplier", 36003)))
        self._input_supplier.pack(side="left", padx=8)

        # ── Section: Column Map ──
        self._section(scroll, "🗂  Column Map")
        map_cols = cfg.get("column_map", {})
        self._inputs_map = {}

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=4)

        fields = list(map_cols.items())
        for i, (field, col) in enumerate(fields):
            row_idx = i // 4
            col_idx = i % 4

            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row_idx, column=col_idx, padx=8, pady=4, sticky="w")

            ctk.CTkLabel(cell, text=field, font=("Segoe UI", 11),
                         text_color=TEXT_MUTED, width=70).pack(side="left")
            ent = ctk.CTkEntry(cell, width=50, font=("Segoe UI", 11),
                               fg_color=CARD_GRAY, border_color=BORDER_GRAY,
                               text_color=WHITE)
            ent.insert(0, col)
            ent.pack(side="left")
            self._inputs_map[field] = ent

        # ── Save Button ──
        ctk.CTkButton(scroll, text="💾  Save Settings",
                      command=self._save_settings,
                      fg_color=GREEN, hover_color="#16A34A",
                      font=("Segoe UI", 14, "bold"), height=44, width=280,
                      corner_radius=10).pack(pady=20)

    def _section(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(14, 6))
        ctk.CTkLabel(frame, text=text, font=("Segoe UI", 14, "bold"),
                     text_color=BLUE).pack(side="left")
        ctk.CTkFrame(frame, height=1, fg_color=BORDER_GRAY).pack(side="left", fill="x", expand=True, padx=10, pady=8)

    def _folder_field(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12),
                     text_color=WHITE, width=260).pack(side="left")
        ent = ctk.CTkEntry(frame, width=380, font=("Segoe UI", 12),
                           fg_color=CARD_GRAY, border_color=BORDER_GRAY, text_color=WHITE)
        ent.insert(0, value)
        ent.pack(side="left", padx=6)
        ctk.CTkButton(frame, text="📂", width=36, height=32,
                      fg_color=BORDER_GRAY, hover_color="#3A3D50",
                      command=lambda e=ent: self._select_folder(e)).pack(side="left")
        return ent

    def _file_field(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12),
                     text_color=WHITE, width=260).pack(side="left")
        ent = ctk.CTkEntry(frame, width=380, font=("Segoe UI", 12),
                           fg_color=CARD_GRAY, border_color=BORDER_GRAY, text_color=WHITE)
        ent.insert(0, value)
        ent.pack(side="left", padx=6)
        ctk.CTkButton(frame, text="📁", width=36, height=32,
                      fg_color=BORDER_GRAY, hover_color="#3A3D50",
                      command=lambda e=ent: self._select_file(e)).pack(side="left")
        return ent

    def _select_folder(self, entry):
        folder = filedialog.askdirectory(title="Select folder")
        if folder:
            entry.delete(0, "end")
            entry.insert(0, folder)

    def _select_file(self, entry):
        file_path = filedialog.askopenfilename(
            title="Select Excel Spreadsheet",
            filetypes=[("Excel", "*.xlsx *.xlsm"), ("All Files", "*.*")]
        )
        if file_path:
            entry.delete(0, "end")
            entry.insert(0, file_path)

    def _save_settings(self):
        cfg = config.load()
        cfg["xml_folder"]       = self._input_cfg_xml.get()
        cfg["processed_folder"] = self._input_cfg_proc.get()
        cfg["excel_file"]       = self._input_cfg_excel.get()
        cfg["sheet_name"]       = self._input_sheet.get()
        cfg["batch_column"]     = self._input_batch.get().upper()
        try:
            cfg["default_supplier"] = int(self._input_supplier.get())
        except ValueError:
            pass

        for field, ent in self._inputs_map.items():
            cfg["column_map"][field] = ent.get().upper()

        config.save(cfg)
        database.log("INFO", "Settings saved.")
        messagebox.showinfo("✅ Success", "Settings saved successfully!")

    # ─────────────────────────────────────────────────────────────────────────
    #  AUDIT LOG TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_log(self):
        f = self.area

        ctk.CTkLabel(f, text="Audit Log", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))
        ctk.CTkLabel(f, text="Complete history of all system operations",
                     font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        # Filters
        filter_frame = ctk.CTkFrame(f, fg_color="transparent")
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))

        self._log_filter = ctk.CTkOptionMenu(
            filter_frame, values=["All", "SUCCESS", "ERROR", "WARNING", "INFO"],
            command=self._filter_log, fg_color=CARD_GRAY,
            button_color=BLUE, button_hover_color=BLUE_HOVER, font=("Segoe UI", 12)
        )
        self._log_filter.pack(side="left")

        ctk.CTkButton(filter_frame, text="🔄 Refresh", command=self._load_log,
                      fg_color=BORDER_GRAY, hover_color="#3A3D50",
                      font=("Segoe UI", 12), width=110, height=32).pack(side="left", padx=8)

        # Header
        header = ctk.CTkFrame(f, fg_color="#252840", corner_radius=8)
        header.pack(fill="x", padx=30, pady=2)
        for txt, w in [("Date/Time", 160), ("Type", 80), ("Message", 400), ("Detail", 300)]:
            ctk.CTkLabel(header, text=txt, font=("Segoe UI", 11, "bold"),
                         text_color=TEXT_MUTED, width=w, anchor="w").pack(side="left", padx=8, pady=6)

        # List
        self._frame_log = ctk.CTkScrollableFrame(f, fg_color=CARD_GRAY, corner_radius=12,
                                                 border_width=1, border_color=BORDER_GRAY)
        self._frame_log.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._all_logs = []
        self._load_log()

    def _load_log(self):
        if not hasattr(self, "_frame_log"):
            return
        self._all_logs = database.list_log(300)
        self._render_log(self._all_logs)

    def _filter_log(self, value):
        if not self._all_logs:
            return
        if value == "All":
            self._render_log(self._all_logs)
        else:
            filtered = [l for l in self._all_logs if l.get("type") == value]
            self._render_log(filtered)

    def _render_log(self, records):
        for w in self._frame_log.winfo_children():
            w.destroy()

        type_colors = {"SUCCESS": GREEN, "ERROR": RED, "WARNING": YELLOW, "INFO": BLUE}

        for i, reg in enumerate(records):
            bg = "#1A1D2E" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._frame_log, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            color_type = type_colors.get(reg.get("type", "INFO"), TEXT_MUTED)
            data = [
                (reg.get("date_time", ""), 160, TEXT_MUTED),
                (reg.get("type", ""), 80, color_type),
                (reg.get("message", "")[:55], 400, WHITE),
                (str(reg.get("detail", ""))[:40], 300, TEXT_MUTED),
            ]
            for txt, w, color in data:
                ctk.CTkLabel(row, text=str(txt), font=("Segoe UI", 11),
                             text_color=color, width=w, anchor="w").pack(side="left", padx=8, pady=3)

    # ─────────────────────────────────────────────────────────────────────────
    #  BACKUPS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_backups(self):
        f = self.area

        ctk.CTkLabel(f, text="Manage Backups", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))
        ctk.CTkLabel(f, text="Automatic backups are created before each processing",
                     font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", padx=30, pady=(0, 15))

        # Action Buttons
        btn_frame = ctk.CTkFrame(f, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkButton(btn_frame, text="🔒  Create Backup Now",
                      command=self._create_manual_backup,
                      fg_color=BLUE, hover_color=BLUE_HOVER,
                      font=("Segoe UI", 13, "bold"), height=40, width=200,
                      corner_radius=8).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_frame, text="🔄  Refresh List",
                      command=self._load_backups,
                      fg_color=BORDER_GRAY, hover_color="#3A3D50",
                      font=("Segoe UI", 13), height=40, width=160,
                      corner_radius=8).pack(side="left")

        # Header
        header = ctk.CTkFrame(f, fg_color="#252840", corner_radius=8)
        header.pack(fill="x", padx=30, pady=2)
        for txt, w in [("Backup Name", 350), ("Size", 100), ("Date/Time", 180), ("Actions", 200)]:
            ctk.CTkLabel(header, text=txt, font=("Segoe UI", 11, "bold"),
                         text_color=TEXT_MUTED, width=w, anchor="w").pack(side="left", padx=8, pady=6)

        # List
        self._frame_bkps = ctk.CTkScrollableFrame(f, fg_color=CARD_GRAY, corner_radius=12,
                                                  border_width=1, border_color=BORDER_GRAY)
        self._frame_bkps.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._load_backups()

    def _create_manual_backup(self):
        cfg = config.load()
        if not cfg.get("excel_file"):
            messagebox.showwarning("Warning", "Configure the Excel file first in ⚙️ Settings.")
            return
        result = backup.create_backup(reason="Manual by user")
        if result:
            messagebox.showinfo("✅ Backup created", f"Backup saved successfully!\n\n{result}")
            self._load_backups()
        else:
            messagebox.showerror("❌ Error", "Could not create the backup. Check the settings.")

    def _load_backups(self):
        if not hasattr(self, "_frame_bkps"):
            return
        for w in self._frame_bkps.winfo_children():
            w.destroy()

        bkps_db   = database.list_backups(30)
        bkps_disk = backup.list_available_backups()

        # Uses disk backups (more complete)
        bkps = bkps_disk if bkps_disk else []

        if not bkps:
            ctk.CTkLabel(self._frame_bkps, text="No backups found.",
                         font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(pady=30)
            return

        for i, bkp in enumerate(bkps):
            bg = "#1A1D2E" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._frame_bkps, fg_color=bg, corner_radius=4)
            row.pack(fill="x", pady=1)

            name = bkp.get("name", "")[:45]
            size = f"{bkp.get('size_kb', 0):,} KB"
            date = bkp.get("date", "")
            path = bkp.get("path", "")

            for txt, w in [(name, 350), (size, 100), (date, 180)]:
                ctk.CTkLabel(row, text=str(txt), font=("Segoe UI", 11),
                             text_color=WHITE, width=w, anchor="w").pack(side="left", padx=8, pady=4)

            ctk.CTkButton(row, text="↩ Restore", width=110, height=28,
                          fg_color=YELLOW, hover_color="#D97706",
                          text_color="#000",
                          font=("Segoe UI", 11, "bold"),
                          command=lambda c=path: self._restore_backup(c)).pack(side="left", padx=4)

    def _restore_backup(self, path):
        confirm = messagebox.askyesno(
            "⚠️ Restore Backup",
            "Are you sure you want to restore this backup?\n\n"
            "The current spreadsheet will be replaced.\n"
            "A backup of the current version will be created automatically beforehand."
        )
        if confirm:
            ok = backup.restore_backup(path)
            if ok:
                messagebox.showinfo("✅ Restored", "Spreadsheet restored successfully!")
            else:
                messagebox.showerror("❌ Error", "Failed to restore. Check the settings.")

    # ─────────────────────────────────────────────────────────────────────────
    #  OUTLOOK TAB (Soon)
    # ─────────────────────────────────────────────────────────────────────────
    def _tab_outlook(self):
        f = self.area

        ctk.CTkLabel(f, text="Outlook Integration", font=("Segoe UI", 24, "bold"),
                     text_color=WHITE).pack(anchor="w", padx=30, pady=(25, 4))

        # Coming soon card
        card = ctk.CTkFrame(f, fg_color=CARD_GRAY, corner_radius=16,
                            border_width=1, border_color=BORDER_GRAY)
        card.pack(expand=True, padx=80, pady=60)

        ctk.CTkLabel(card, text="📧", font=("Segoe UI Emoji", 60)).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="Email Automation in Development",
                     font=("Segoe UI", 20, "bold"), text_color=WHITE).pack()
        ctk.CTkLabel(card, text="Soon you will be able to connect directly to the corporate Outlook\nand automatically save XMLs received by email.",
                     font=("Segoe UI", 13), text_color=TEXT_MUTED,
                     justify="center").pack(pady=10)

        features = [
            "✅  Automatically monitor Outlook folder",
            "✅  Download XMLs from emails with specific subjects",
            "✅  Process 100% automatically without intervention",
            "✅  Email notification after processing",
        ]
        for item in features:
            ctk.CTkLabel(card, text=item, font=("Segoe UI", 12), text_color=BLUE).pack(anchor="w", padx=40, pady=2)

        ctk.CTkLabel(card, text="\n🔜  Version 3.0 — Under construction",
                     font=("Segoe UI", 12, "bold"), text_color=YELLOW).pack(pady=(10, 30))


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = InvoiceSystemApp()
    app.mainloop()
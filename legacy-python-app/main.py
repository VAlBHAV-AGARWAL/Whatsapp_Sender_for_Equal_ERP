"""WhatsApp Message OS - Main GUI Application."""

import json
import logging
import os
import random
import threading
import time
import tkinter as tk
from importlib.util import find_spec
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

import customtkinter as ctk

from data_handler import DataHandler
from whatsapp_bot import WhatsAppBot

HAS_DRAG_DROP = find_spec("tkinterdnd2") is not None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class WhatsAppMessengerApp(ctk.CTk):
    """Desktop app for sending WhatsApp due-payment reminders."""

    def __init__(self):
        super().__init__()

        self.title("📱 WhatsApp Bulk Messenger Pro")
        self.geometry("1200x900")
        self.resizable(True, True)

        # Set modern dark theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.config_file = "config.json"
        self.config = self.load_config()

        self.selected_file = ctk.StringVar(value="")
        self.running = False
        self.stop_requested = False
        self.current_bills_data = None
        self.party_phone_map = {}
        self.connection_validated = False

        # Country code mapping
        self.country_map = {
            "+91 (India)": "+91",
            "+1 (USA)": "+1",
            "+44 (UK)": "+44",
            "+81 (Japan)": "+81",
            "+86 (China)": "+86",
        }
        saved_country = self.config.get("country_code", "+91")
        self.country_var = ctk.StringVar(
            value=next((k for k, v in self.country_map.items() if v == saved_country), "+91 (India)")
        )

        self.create_widgets()
        self.center_window()

        if HAS_DRAG_DROP:
            self.setup_drag_drop()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES

            if not hasattr(self, "drop_target_register"):
                self.log_message("Warning: Drag and drop is not available on this system build.")
                return

            self.drop_target_register(DND_FILES)
            self.bind("<<Drop>>", self.drop_handler)
            self.log_message("OK: Drag and drop enabled.")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.log_message(f"Warning: Drag and drop disabled: {exc}")

    def drop_handler(self, event):
        files = self.parse_dnd_files(event.data)
        if not files:
            return

        file_path = files[0]
        if file_path.lower().endswith((".xlsx", ".xls", ".csv")):
            self.selected_file.set(file_path)
            self.config["last_file"] = file_path
            self.file_label.configure(text=file_path)
            self.log_message(f"OK: File dropped: {Path(file_path).name}")
            self.load_and_preview_file(file_path)
        else:
            self.log_message("Error: Invalid file type. Please use .xlsx, .xls, or .csv")

    @staticmethod
    def parse_dnd_files(data):
        if "{" in data:
            return data.replace("{", "").replace("}", "").split()
        return data.split()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as handle:
                    return json.load(handle)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logging.error("Error loading config: %s", exc)

        return {
            "last_file": "",
            "min_days": 60,
            "message_template": (
                "Hi {Party}, your bill {BILLNO} of amount Rs.{BALAMT} is pending "
                "for {DAYS} days. Please arrange payment at your earliest."
            ),
            "country_code": "+91",
        }

    def save_config(self):
        try:
            if hasattr(self, "days_entry") and self.days_entry.winfo_exists():
                self.config["min_days"] = int(self.days_entry.get())
            self.config["message_template"] = self.template_text.get("1.0", "end-1c")
            self.config["country_code"] = self.get_selected_country_code()
            with open(self.config_file, "w", encoding="utf-8") as handle:
                json.dump(self.config, handle, indent=4, ensure_ascii=False)
            self.log_message("OK: Settings saved")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            messagebox.showerror("Error", f"Failed to save settings: {exc}")
            logging.error("Config save error: %s", exc)

    def get_selected_country_code(self):
        return self.country_map.get(self.country_var.get(), self.config.get("country_code", "+91"))

    def create_widgets(self):
        # Main container
        main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1a1a1a")
        main_frame.pack(padx=15, pady=15, fill="both", expand=True)

        # Top Navigation Bar
        nav_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=35)
        nav_frame.pack(fill="x", pady=(0, 15))

        browse_btn = ctk.CTkButton(
            nav_frame,
            text="📂 Browse",
            command=self.browse_file,
            fg_color="#3182ce",
            hover_color="#2c5282",
            height=32,
            width=120,
            font=("Segoe UI", 11, "bold")
        )
        browse_btn.pack(side="left", padx=(0, 15))

        settings_btn = ctk.CTkButton(
            nav_frame,
            text="⚙️ Manage Settings",
            command=self.show_settings_dialog,
            fg_color="#2d3748",
            hover_color="#3d4758",
            height=32,
            width=150,
            font=("Segoe UI", 11, "bold")
        )
        settings_btn.pack(side="left")

        self.file_label = ctk.CTkLabel(
            nav_frame,
            text=self.config.get("last_file", "No file selected"),
            text_color="#a0aec0",
            font=("Segoe UI", 9),
            wraplength=400
        )
        self.file_label.pack(side="left", fill="x", expand=True, padx=(15, 0))

        # Data preview section - Party Summary
        preview_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        preview_frame.pack(fill="both", expand=True, pady=(0, 12))

        preview_title = ctk.CTkLabel(
            preview_frame,
            text="Party Summary",
            font=("Segoe UI", 13, "bold"),
            text_color="#e2e8f0"
        )
        preview_title.pack(anchor="w", pady=(0, 8))

        table_container = ctk.CTkFrame(preview_frame, fg_color="#2d3748", corner_radius=8)
        table_container.pack(fill="both", expand=True)

        # Style the treeview
        style = ttk.Style()
        style.configure("Treeview",
            background="#1a202c",
            foreground="#e2e8f0",
            fieldbackground="#1a202c",
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.configure("Treeview.Heading",
            background="#2d3748",
            foreground="#e2e8f0",
            borderwidth=0,
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview",
            background=[('selected', '#3182ce')],
            foreground=[('selected', '#ffffff')]
        )

        self.bills_tree = ttk.Treeview(
            table_container,
            columns=("Party", "Bills", "Total Amount", "Days", "Phone"),
            show="headings",
            height=6,
        )

        self.bills_tree.heading("Party", text="Party")
        self.bills_tree.heading("Bills", text="Bills")
        self.bills_tree.heading("Total Amount", text="Amount (₹)")
        self.bills_tree.heading("Days", text="Days")
        self.bills_tree.heading("Phone", text="Phone")

        self.bills_tree.column("Party", width=180)
        self.bills_tree.column("Bills", width=150)
        self.bills_tree.column("Total Amount", width=100)
        self.bills_tree.column("Days", width=70)
        self.bills_tree.column("Phone", width=140)

        v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.bills_tree.yview)
        self.bills_tree.configure(yscroll=v_scrollbar.set)
        self.bills_tree.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        v_scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        # Message template section
        template_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        template_frame.pack(fill="both", pady=(0, 12))

        template_title = ctk.CTkLabel(
            template_frame,
            text="Message Template",
            font=("Segoe UI", 13, "bold"),
            text_color="#e2e8f0"
        )
        template_title.pack(anchor="w", pady=(8, 4))

        variables_label = ctk.CTkLabel(
            template_frame,
            text="Variables: {Party}, {BILLNO}, {BALAMT}, {DAYS}",
            text_color="#a0aec0",
            font=("Segoe UI", 8, "italic")
        )
        variables_label.pack(anchor="w", pady=(0, 4))

        template_input = ctk.CTkFrame(template_frame, fg_color="#2d3748", corner_radius=8)
        template_input.pack(fill="both", expand=False, pady=(0, 8))

        self.template_text = scrolledtext.ScrolledText(
            template_input,
            height=4,
            font=("Consolas", 9),
            bg="#1a1a1a",
            fg="#e2e8f0",
            insertbackground="#00d4aa",
            wrap="word",
            padx=8,
            pady=8
        )
        self.template_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.template_text.insert(
            "1.0",
            self.config.get(
                "message_template",
                "Dear {Party}, Your bill {BILLNO} for ₹{BALAMT} is pending {DAYS} days. Please pay.",
            ),
        )

        # Save button next to template
        save_template_btn = ctk.CTkButton(
            template_frame,
            text="💾 Save Template",
            command=self.save_config,
            fg_color="#2d3748",
            hover_color="#3d4758",
            height=28,
            font=("Segoe UI", 9, "bold")
        )
        save_template_btn.pack(pady=(0, 12))

        # Control buttons section - No header, just buttons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 12))

        self.connect_button = ctk.CTkButton(
            buttons_frame,
            text="🔗 Connect WhatsApp",
            command=self.connect_whatsapp,
            fg_color="#3182ce",
            hover_color="#2c5282",
            height=36,
            font=("Segoe UI", 11, "bold")
        )
        self.connect_button.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="▶️ Start",
            command=self.start_sending,
            fg_color="#22c55e",
            hover_color="#16a34a",
            font=("Segoe UI", 11, "bold"),
            height=36,
        )
        self.start_button.pack(side="left", padx=(0, 10), fill="x", expand=True)

        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="⏹️ Stop",
            command=self.stop_sending,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=("Segoe UI", 11, "bold"),
            height=36,
            state="disabled",
        )
        self.stop_button.pack(side="left", fill="x", expand=True)

        # Connection status
        self.connection_status_label = ctk.CTkLabel(
            buttons_frame,
            text="",
            text_color="#a0aec0",
            font=("Segoe UI", 8),
        )

        # Activity log - Simplified for non-technical users
        log_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        log_frame.pack(fill="both", expand=True)

        log_title = ctk.CTkLabel(
            log_frame,
            text="Status",
            font=("Segoe UI", 13, "bold"),
            text_color="#e2e8f0"
        )
        log_title.pack(anchor="w", pady=(8, 4))

        log_container = ctk.CTkFrame(log_frame, fg_color="#2d3748", corner_radius=8)
        log_container.pack(fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=8,
            font=("Consolas", 9),
            bg="#1a1a1a",
            fg="#e2e8f0",
            insertbackground="#00d4aa",
            state="disabled",
            wrap="word",
            padx=8,
            pady=8
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Configure text tags for colored output
        self.log_text.tag_configure("sent", foreground="#22c55e", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("failed", foreground="#ef4444", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("info", foreground="#60a5fa")

        # Bind events
        self.bills_tree.bind("<Double-1>", self.on_tree_double_click)
        self.bills_tree.bind("<Button-3>", self.show_context_menu)

        self.log_message("Ready to send messages", "info")

    def connect_whatsapp(self):
        """Validate WhatsApp Web connection."""
        if self.running:
            messagebox.showwarning("Warning", "Cannot connect while sending is in progress")
            return

        self.connect_button.configure(state="disabled", text="🔄 CONNECTING...")
        self.connection_status_label.configure(text="🔄 Opening WhatsApp Web...", text_color="#fbbf24")
        self.update()

        def validate_connection():
            try:
                # Always open WhatsApp Web first
                import webbrowser
                webbrowser.open("https://web.whatsapp.com/")
                
                # Give it time to load
                time.sleep(8)
                
                bot = WhatsAppBot(log_callback=self.log_message)
                if bot.validate_connection():
                    self.connection_validated = True
                    self.connect_button.configure(text="✅ Connected", fg_color="#22c55e", hover_color="#16a34a")
                    self.log_message("WhatsApp connected and ready to send", "sent")
                else:
                    self.connection_validated = False
                    self.connect_button.configure(text="🔗 Connect WhatsApp", fg_color="#3182ce", hover_color="#2c5282")
                    self.log_message("WhatsApp connection failed - please try again", "failed")
            except Exception as exc:
                self.connection_validated = False
                self.connect_button.configure(text="🔗 Connect WhatsApp", fg_color="#3182ce", hover_color="#2c5282")
                self.log_message(f"Connection error: {str(exc)[:50]}", "failed")
            finally:
                self.connect_button.configure(state="normal")

        # Run validation in background thread
        thread = threading.Thread(target=validate_connection, daemon=True)
        thread.start()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel/CSV Report",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return

        self.selected_file.set(file_path)
        self.config["last_file"] = file_path
        self.file_label.configure(text=file_path)
        self.log_message(f"OK: File selected: {Path(file_path).name}")
        self.load_and_preview_file(file_path)

    def load_and_preview_file(self, file_path):
        try:
            handler = DataHandler(file_path, country_code=self.get_selected_country_code())
            df = handler.parse_file()
            if df is None or df.empty:
                self.log_message("Error: Failed to parse file or file is empty")
                return

            self.current_bills_data = df
            self.party_phone_map = {}
            self.log_message(f"OK: Loaded {len(df)} bills from file")

            for item in self.bills_tree.get_children():
                self.bills_tree.delete(item)

            party_summary = df.groupby("Party").agg(
                {
                    "BILLNO": lambda x: ", ".join(x.astype(str)),
                    "BALAMT": "sum",
                    "DAYS": "max",
                    "PHONE_NUMBERS": lambda x: list(set([phone for phones in x.dropna() for phone in (phones if phones else [])])),
                }
            ).reset_index()

            for idx, row in party_summary.iterrows():
                party = row["Party"]
                phone_numbers = row["PHONE_NUMBERS"]
                
                # Display logic: show count if multiple phones, otherwise show the phone
                if phone_numbers and len(phone_numbers) > 1:
                    display_phone = f"{len(phone_numbers)} phones"
                elif phone_numbers and len(phone_numbers) == 1:
                    display_phone = phone_numbers[0]
                else:
                    display_phone = "Not found"
                
                self.bills_tree.insert(
                    "",
                    "end",
                    iid=f"party_{idx}",
                    values=(
                        party,
                        row["BILLNO"],
                        f"Rs.{row['BALAMT']:.2f}",
                        f"{int(row['DAYS'])} days",
                        display_phone,
                    ),
                )
                self.party_phone_map[party] = {
                    "original": phone_numbers.copy() if phone_numbers else [],
                    "current": phone_numbers.copy() if phone_numbers else []
                }

            self.log_message(f"OK: Preview loaded: {len(party_summary)} parties ready to send")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.log_message(f"Error loading file: {exc}")
            logging.error("Preview load error: %s", exc, exc_info=True)

    def on_tree_double_click(self, event):
        selection = self.bills_tree.selection()
        if not selection:
            return

        item = selection[0]
        col = self.bills_tree.identify_column(event.x)
        if col != "#5":
            return

        values = list(self.bills_tree.item(item, "values"))
        party_name = values[0]
        current_phones = self.party_phone_map[party_name]["current"]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Phones for {party_name}")
        dialog.geometry("500x350")

        # Center the dialog on the main window
        dialog.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        dialog_width = 500
        dialog_height = 350
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        ctk.CTkLabel(dialog, text=f"Party: {party_name}", font=("Arial", 12, "bold")).pack(padx=12, pady=10)
        ctk.CTkLabel(
            dialog,
            text="Phone numbers (10 digits each, country code will be added):",
            font=("Arial", 10),
        ).pack(padx=12, pady=(0, 8))

        # Frame for phone entries
        phones_frame = ctk.CTkScrollableFrame(dialog, height=200)
        phones_frame.pack(padx=12, pady=6, fill="both", expand=True)

        phone_entries = []
        cc = self.get_selected_country_code()

        # Create entry for each existing phone
        for i, phone in enumerate(current_phones or []):
            frame = ctk.CTkFrame(phones_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            display_phone = ""
            if phone and str(phone).startswith("+"):
                display_phone = str(phone)[len(cc):]
            
            entry = ctk.CTkEntry(frame, font=("Arial", 11), placeholder_text="10 digits only")
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            entry.insert(0, display_phone)
            
            def remove_phone(idx=i):
                if len(phone_entries) > 1:  # Keep at least one entry
                    phone_entries[idx]["frame"].destroy()
                    del phone_entries[idx]
                    # Re-index remaining entries
                    for j, entry_data in enumerate(phone_entries):
                        entry_data["index"] = j
            
            remove_btn = ctk.CTkButton(frame, text="×", width=30, height=30, 
                                     command=remove_phone, fg_color="#dc3545", hover_color="#c82333")
            remove_btn.pack(side="right")
            
            phone_entries.append({"entry": entry, "frame": frame, "index": i})

        # Add phone button
        def add_phone():
            frame = ctk.CTkFrame(phones_frame, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            
            entry = ctk.CTkEntry(frame, font=("Arial", 11), placeholder_text="10 digits only")
            entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            def remove_phone_entry():
                if len(phone_entries) > 1:  # Keep at least one entry
                    frame.destroy()
                    phone_entries.remove(next(e for e in phone_entries if e["frame"] == frame))
            
            remove_btn = ctk.CTkButton(frame, text="×", width=30, height=30, 
                                     command=remove_phone_entry, fg_color="#dc3545", hover_color="#c82333")
            remove_btn.pack(side="right")
            
            phone_entries.append({"entry": entry, "frame": frame})

        add_btn = ctk.CTkButton(phones_frame, text="+ Add Phone", command=add_phone, 
                               fg_color="#28a745", hover_color="#218838", height=32)
        add_btn.pack(pady=5)

        def save_phones():
            new_phones = []
            cc = self.get_selected_country_code()
            
            for entry_data in phone_entries:
                phone_raw = entry_data["entry"].get().strip()
                if phone_raw:
                    if not (phone_raw.isdigit() and len(phone_raw) == 10):
                        messagebox.showerror("Error", f"Phone number '{phone_raw}' must be exactly 10 digits")
                        return
                    new_phones.append(f"{cc}{phone_raw}")
            
            if not new_phones:
                messagebox.showerror("Error", "At least one valid phone number is required")
                return

            # Update display
            if len(new_phones) > 1:
                display_text = f"{len(new_phones)} phones"
            else:
                display_text = new_phones[0]
            
            values[4] = display_text
            self.bills_tree.item(item, values=values)

            # Update data structures
            self.party_phone_map[party_name]["current"] = new_phones
            if self.current_bills_data is not None:
                # Update all rows for this party with new phone numbers
                party_mask = self.current_bills_data["Party"] == party_name
                self.current_bills_data.loc[party_mask, "PHONE_NUMBERS"] = [new_phones] * party_mask.sum()
                self.current_bills_data.loc[party_mask, "PHONE_NUMBER"] = new_phones[0]

            self.log_message(f"OK: Updated phones for {party_name}: {len(new_phones)} numbers")
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save", command=save_phones, height=36).pack(padx=12, pady=10, fill="x")

    def show_context_menu(self, event):
        """Show right-click context menu for treeview rows."""
        item = self.bills_tree.identify_row(event.y)
        if not item:
            return

        self.bills_tree.selection_set(item)

        # Create context menu
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Edit Phone Numbers", command=self.edit_party_phone)
        menu.add_separator()
        menu.add_command(label="Remove Row", command=self.remove_party_row)

        menu.post(event.x_root, event.y_root)

    def edit_party_phone(self):
        """Edit phone numbers for selected party (alternative to double-click)."""
        selection = self.bills_tree.selection()
        if not selection:
            return
        
        # Directly call the double-click handler with simulated event
        item = selection[0]
        # Create a mock event object for the phone column (column 5)
        class MockEvent:
            def __init__(self, x):
                self.x = x
        
        mock_event = MockEvent(400)  # Position in phone column
        # Temporarily set selection and call double-click handler
        original_selection = self.bills_tree.selection()
        self.bills_tree.selection_set(item)
        self.on_tree_double_click(mock_event)
        # Restore original selection if needed
        if original_selection:
            self.bills_tree.selection_set(original_selection)

    def remove_party_row(self):
        """Remove selected party row from treeview and data."""
        selection = self.bills_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.bills_tree.item(item, "values")
        party_name = values[0]

        # Confirmation dialog
        if not messagebox.askyesno("Confirm Removal", 
                                 f"Remove '{party_name}' from the send list?\n\nThis will permanently remove this party from the current session."):
            return

        # Remove from treeview
        self.bills_tree.delete(item)

        # Remove from party_phone_map
        if party_name in self.party_phone_map:
            del self.party_phone_map[party_name]

        # Remove from current_bills_data if it exists
        if self.current_bills_data is not None:
            self.current_bills_data = self.current_bills_data[self.current_bills_data["Party"] != party_name].reset_index(drop=True)

        self.log_message(f"OK: Removed party '{party_name}' from send list")

    def show_settings_dialog(self):
        """Show settings dialog for Min Days and Country Code"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        dialog_width = 400
        dialog_height = 250
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Minimum Days
        days_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        days_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(days_frame, text="Minimum Days Outstanding:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        
        days_entry = ctk.CTkEntry(
            days_frame,
            width=100,
            height=32,
            font=("Segoe UI", 10)
        )
        days_entry.pack(anchor="w", pady=(5, 0))
        days_entry.insert(0, str(self.config.get("min_days", 60)))

        # Country Code
        country_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        country_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(country_frame, text="Country Code:", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        
        country_combo = ctk.CTkComboBox(
            country_frame,
            values=list(self.country_map.keys()),
            variable=self.country_var,
            width=200,
            height=32,
            font=("Segoe UI", 10),
            state="readonly",
            fg_color="#2d3748",
            button_color="#3182ce",
            button_hover_color="#2c5282"
        )
        country_combo.pack(anchor="w", pady=(5, 0))

        # Save button
        def save_settings():
            try:
                min_days = int(days_entry.get())
                if min_days < 0:
                    messagebox.showerror("Error", "Days must be non-negative")
                    return
                
                self.config["min_days"] = min_days
                self.config["country_code"] = self.get_selected_country_code()
                self.save_config()
                messagebox.showinfo("Success", "Settings saved!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Days must be a valid number")

        save_btn = ctk.CTkButton(
            dialog,
            text="Save Settings",
            command=save_settings,
            fg_color="#22c55e",
            hover_color="#16a34a",
            height=36,
            font=("Segoe UI", 11, "bold")
        )
        save_btn.pack(padx=20, pady=20, fill="x")

    def log_message(self, message, tag="info"):
        """Log message with optional color tag (sent=green, failed=red, info=blue)"""
        # Filter technical messages - only show to end-users what matters
        if message.startswith("OK:") or message.startswith("WARNING:") or message.startswith("ERROR: Connection") or "initialization" in message.lower():
            return
        
        self.log_text.config(state="normal")
        
        # Format business-friendly messages
        if "Message sent" in message or "sent successfully" in message:
            display_msg = f"✅ {message.replace('OK: Message sent successfully', 'Sent').replace('sent to ', 'to ')}"
            tag = "sent"
        elif "Failed to send" in message or "ERROR:" in message:
            display_msg = f"❌ {message.replace('ERROR: ', '').replace('Failed to send to ', 'Failed: ')}"
            tag = "failed"
        elif "Extracting" in message or "Filtering" in message or "Reading" in message or "Loaded" in message:
            # Technical setup messages - show simplified version
            if "Extracted" in message:
                display_msg = message  # Show data extraction results
                tag = "info"
            else:
                return  # Skip other technical messages
        else:
            # Show other important business messages
            if message.startswith("Ready") or message.startswith("===") or "Bill" in message or "SEND" in message:
                display_msg = message.replace("===", "").strip()
                tag = "info"
            else:
                display_msg = message
        
        self.log_text.insert("end", f"\n{display_msg}", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start_sending(self):
        if self.running:
            messagebox.showwarning("Warning", "Process already running")
            return
        if not self.selected_file.get():
            messagebox.showerror("Error", "Please select an Excel/CSV file first")
            return
        if not self.connection_validated:
            messagebox.showerror("Error", "Please connect to WhatsApp first using the CONNECT button")
            return

        try:
            min_days = int(self.config.get("min_days", 60))
        except (TypeError, ValueError):
            min_days = 60

        if min_days < 0:
            messagebox.showerror("Error", "Minimum Days must be non-negative")
            return

        template = self.template_text.get("1.0", "end-1c").strip()
        if not template:
            messagebox.showerror("Error", "Please enter a message template")
            return

        self.save_config()
        self.running = True
        self.stop_requested = False
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        country_code = self.get_selected_country_code()
        thread = threading.Thread(
            target=self.run_sending_process,
            args=(self.selected_file.get(), min_days, template, country_code),
            daemon=True,
        )
        thread.start()

    def stop_sending(self):
        if not self.running:
            self.log_message("No active sending process to stop.")
            return
        self.stop_requested = True
        self.stop_button.configure(state="disabled")
        self.log_message("Stop requested. Finishing current step and stopping...")

    def run_sending_process(self, file_path, min_days, template, country_code):
        bot = None
        try:
            self.log_message("=" * 60)
            self.log_message("STARTING SEND PROCESS")
            self.log_message("=" * 60)

            if self.current_bills_data is not None:
                self.log_message("\nUsing loaded file data (with manual edits)")
                df = self.current_bills_data.copy()
                self.log_message(f"OK: Using {len(df)} bills from preview")
            else:
                self.log_message(f"\nReading file: {Path(file_path).name}")
                df = DataHandler(file_path, country_code).parse_file()
                if df is None or df.empty:
                    self.log_message("ERROR: No data extracted from file. Please check file format.")
                    return
                self.log_message(f"OK: Extracted {len(df)} total rows")

            self.log_message(f"\nFiltering bills outstanding >= {min_days} days...")
            handler = DataHandler(file_path, country_code)
            filtered_df, accounts_without_phone = handler.filter_by_days(df, min_days)

            if filtered_df.empty:
                self.log_message(f"WARNING: No bills found with >= {min_days} days outstanding.")
                self.log_message("Process complete.")
                return

            self.log_message(f"OK: Found {len(filtered_df)} matching bills to send")

            if not accounts_without_phone.empty:
                self.log_message("\nWARNING: ACCOUNTS WITHOUT PHONE NUMBERS (Excluded):")
                for _, row in accounts_without_phone.iterrows():
                    self.log_message(f" - {row['Party']}: Bills {row['BILLNO']} ({row['DAYS']})")

            self.log_message("\nBILLS TO SEND (Preview):")
            account_summary = filtered_df.groupby("Party").agg(
                {"BILLNO": lambda x: ", ".join(x.astype(str)), "DAYS": "max", "BALAMT": "sum"}
            ).reset_index()

            total_outstanding = 0.0
            for _, row in account_summary.iterrows():
                total_outstanding += float(row["BALAMT"])
                self.log_message(
                    f" - {row['Party']}: Bills {row['BILLNO']} | Total: Rs.{row['BALAMT']:.2f}"
                )

            self.log_message(f"\nTOTAL OUTSTANDING AMOUNT: Rs.{total_outstanding:.2f}")

            self.log_message("\nInitializing WhatsApp sender...")
            bot = WhatsAppBot(log_callback=self.log_message)

            self.log_message("\nSENDING MESSAGES...")
            self.log_message("-" * 60)

            success_count = 0
            failed_count = 0
            sent_phones = set()
            sent_since_long_break = 0
            next_long_break_after = random.randint(20, 30)

            party_recipients = filtered_df.groupby("Party").agg(
                {
                    "BILLNO": lambda x: ", ".join(x.astype(str)),
                    "DAYS": "max",
                    "BALAMT": "sum",
                    "PHONE_NUMBERS": lambda x: list(set([phone for phones in x.dropna() for phone in (phones if phones else [])])),
                }
            ).reset_index()

            self.log_message(f"Unique parties to send: {len(party_recipients)}")

            for _, row in party_recipients.iterrows():
                if self.stop_requested:
                    self.log_message("\nStop requested by user. Stopping before next message.")
                    break

                try:
                    message = template
                    for col in row.index:
                        if col != "PHONE_NUMBERS":  # Skip phone numbers in template replacement
                            message = message.replace(f"{{{col}}}", str(row[col]))

                    party = row.get("Party", "Customer")
                    phone_numbers = row.get("PHONE_NUMBERS", [])

                    if not phone_numbers:
                        self.log_message(f"\nWARNING: Skipping {party}: No valid phone numbers")
                        failed_count += 1
                        continue

                    # Send to all phone numbers for this party
                    party_success_count = 0
                    party_failed_count = 0
                    
                    for phone in phone_numbers:
                        if phone in sent_phones:
                            self.log_message(f"\nWARNING: Skipping duplicate phone for {party}: {phone}")
                            continue

                        self.log_message(f"\nSending to: {party} ({row.get('DAYS', '?')} days) - Phone: {phone}")
                        self.log_message(f" Message: {message[:70]}...")

                        try:
                            bot.send_message(phone, message)
                            self.log_message("OK: Message sent successfully")
                            success_count += 1
                            party_success_count += 1
                            sent_phones.add(phone)
                        except Exception as send_exc:
                            self.log_message(f"ERROR: Failed to send to {phone}: {send_exc}")
                            failed_count += 1
                            party_failed_count += 1
                            bot.invalidate_connection()  # Mark connection as invalid on send failure

                        # Delay between messages to same party (shorter delay)
                        if len(phone_numbers) > 1:
                            delay = random.randint(5, 15)
                            self.log_message(f"WAIT: {delay}s before next phone for {party}...")
                            for i in range(delay):
                                if self.stop_requested:
                                    self.log_message(" Stop requested during wait delay.")
                                    break
                                time.sleep(1)
                                if (i + 1) % 5 == 0 and i < delay - 1:
                                    self.log_message(f" {delay - i}s remaining...")

                        if self.stop_requested:
                            break

                    if len(phone_numbers) > 1:
                        self.log_message(f"Party {party}: Sent to {party_success_count} phones, failed {party_failed_count}")

                    sent_since_long_break += len(phone_numbers)
                    sent_since_long_break += 1

                    delay = random.randint(25, 45)
                    self.log_message(f"WAIT: {delay}s before next message...")
                    for i in range(delay):
                        if self.stop_requested:
                            self.log_message(" Stop requested during wait delay.")
                            break
                        time.sleep(1)
                        if (i + 1) % 5 == 0 and i < delay - 1:
                            self.log_message(f" {delay - i}s remaining...")

                    if self.stop_requested:
                        self.log_message(" Stopping send loop now.")
                        break

                    if sent_since_long_break >= next_long_break_after:
                        break_minutes = random.randint(5, 10)
                        break_seconds = break_minutes * 60
                        self.log_message(
                            f" Cooling break: pausing for {break_minutes} minutes after {sent_since_long_break} sends."
                        )
                        for i in range(break_seconds):
                            if self.stop_requested:
                                self.log_message(" Stop requested during cooling break.")
                                break
                            time.sleep(1)
                            if (i + 1) % 60 == 0 and i < break_seconds - 1:
                                remaining = (break_seconds - i - 1) // 60
                                self.log_message(f" {remaining} min remaining...")

                        if self.stop_requested:
                            self.log_message(" Stopping send loop now.")
                            break

                        sent_since_long_break = 0
                        next_long_break_after = random.randint(20, 30)

                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self.log_message(f"ERROR: {exc}")
                    failed_count += 1
                    logging.error("Send error: %s", exc)

            self.log_message("\n" + "=" * 60)
            self.log_message("SEND PROCESS COMPLETE!")
            self.log_message(f"Sent: {success_count}")
            self.log_message(f"Failed: {failed_count}")
            self.log_message(f"Total parties processed: {len(party_recipients)}")
            if self.stop_requested:
                self.log_message("Status: Stopped by user")
            self.log_message("=" * 60)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.log_message(f"\nCRITICAL ERROR: {exc}")
            logging.error("Process error: %s", exc, exc_info=True)
        finally:
            if bot is not None:
                bot.close()
            self.running = False
            self.stop_requested = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def on_closing(self):
        self.save_config()
        self.destroy()


def main():
    app = WhatsAppMessengerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()

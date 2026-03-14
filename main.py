"""WhatsApp Message OS - Main GUI Application."""

import json
import logging
import os
import random
import threading
import time
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

        self.title("WhatsApp Payment Reminder")
        self.geometry("1080x860")
        self.resizable(True, True)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.config_file = "config.json"
        self.config = self.load_config()

        self.selected_file = ctk.StringVar(value="")
        self.running = False
        self.stop_requested = False
        self.current_bills_data = None
        self.party_phone_map = {}

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
            self.config["min_days"] = int(self.days_entry.get())
            self.config["message_template"] = self.template_text.get("1.0", "end-1c")
            self.config["country_code"] = self.country_map.get(self.country_var.get(), "+91")
            with open(self.config_file, "w", encoding="utf-8") as handle:
                json.dump(self.config, handle, indent=4, ensure_ascii=False)
            self.log_message("OK: Settings saved")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            messagebox.showerror("Error", f"Failed to save settings: {exc}")
            logging.error("Config save error: %s", exc)

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, corner_radius=12)
        main_frame.pack(padx=16, pady=16, fill="both", expand=True)

        file_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        file_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(file_frame, text="Select Excel/CSV File", font=("Arial", 14, "bold")).pack(
            anchor="w", padx=12, pady=(10, 6)
        )

        browse_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        browse_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(browse_row, text="Browse File", command=self.browse_file, width=130, height=36).pack(
            side="left", padx=(0, 10)
        )

        self.file_label = ctk.CTkLabel(
            browse_row,
            text=self.config.get("last_file", "No file selected"),
            text_color="gray75",
            font=("Arial", 11),
        )
        self.file_label.pack(side="left", fill="x", expand=True)

        preview_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        preview_frame.pack(fill="both", expand=True, pady=(0, 12))
        ctk.CTkLabel(
            preview_frame,
            text="Party Summary (Double-click phone to edit)",
            font=("Arial", 13, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 6))

        table_frame = ctk.CTkFrame(preview_frame, fg_color="gray20")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.bills_tree = ttk.Treeview(
            table_frame,
            columns=("Party", "Bills", "Total Amount", "Days", "Phone"),
            show="headings",
            height=6,
        )
        self.bills_tree.heading("Party", text="Party")
        self.bills_tree.heading("Bills", text="Bills")
        self.bills_tree.heading("Total Amount", text="Total Amount (Rs.)")
        self.bills_tree.heading("Days", text="Days")
        self.bills_tree.heading("Phone", text="Phone (Editable)")

        self.bills_tree.column("Party", width=190)
        self.bills_tree.column("Bills", width=160)
        self.bills_tree.column("Total Amount", width=145)
        self.bills_tree.column("Days", width=90)
        self.bills_tree.column("Phone", width=180)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.bills_tree.yview)
        self.bills_tree.configure(yscroll=scrollbar.set)
        self.bills_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        settings_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        settings_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(settings_frame, text="Settings", font=("Arial", 13, "bold")).pack(
            anchor="w", padx=12, pady=(10, 6)
        )

        settings_row = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(settings_row, text="Min Days:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.days_entry = ctk.CTkEntry(settings_row, width=80)
        self.days_entry.pack(side="left", padx=(0, 14))
        self.days_entry.insert(0, str(self.config.get("min_days", 60)))

        ctk.CTkLabel(settings_row, text="Country Code:", font=("Arial", 10)).pack(side="left", padx=(0, 5))

        self.country_map = {
            "+91 (India)": "+91",
            "+1 (USA)": "+1",
            "+44 (UK)": "+44",
            "+81 (Japan)": "+81",
            "+86 (China)": "+86",
        }
        self.country_var = ctk.StringVar()
        saved_code = self.config.get("country_code", "+91")
        self.country_var.set(next((k for k, v in self.country_map.items() if v == saved_code), "+91 (India)"))

        self.country_combo = ctk.CTkComboBox(
            settings_row,
            values=list(self.country_map.keys()),
            variable=self.country_var,
            width=150,
            state="readonly",
        )
        self.country_combo.pack(side="left")

        template_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        template_frame.pack(fill="both", expand=True, pady=(0, 12))
        ctk.CTkLabel(template_frame, text="Message Template", font=("Arial", 13, "bold")).pack(
            anchor="w", padx=12, pady=(10, 6)
        )
        ctk.CTkLabel(
            template_frame,
            text="Variables: {Party}, {BILLNO}, {BALAMT}, {DAYS}",
            text_color="gray65",
            font=("Arial", 9, "italic"),
        ).pack(anchor="w", padx=12, pady=(0, 6))

        self.template_text = scrolledtext.ScrolledText(
            template_frame,
            height=5,
            font=("Courier", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
            wrap="word",
        )
        self.template_text.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.template_text.insert(
            "1.0",
            self.config.get(
                "message_template",
                "Hi {Party}, your bill {BILLNO} of amount Rs.{BALAMT} is pending for {DAYS} days.",
            ),
        )

        actions = ctk.CTkFrame(main_frame, fg_color="gray25")
        actions.pack(fill="x", pady=(0, 12))

        ctk.CTkButton(
            actions,
            text="Save Settings",
            command=self.save_config,
            fg_color="#465364",
            hover_color="#546273",
            height=36,
        ).pack(side="left", padx=12, pady=10, fill="x", expand=True)

        self.start_button = ctk.CTkButton(
            actions,
            text="START SENDING",
            command=self.start_sending,
            fg_color="#0b8f3a",
            hover_color="#0ea848",
            font=("Arial", 12, "bold"),
            height=36,
        )
        self.start_button.pack(side="left", padx=(0, 12), pady=10, fill="x", expand=True)

        self.stop_button = ctk.CTkButton(
            actions,
            text="STOP SENDING",
            command=self.stop_sending,
            fg_color="#b00020",
            hover_color="#d00030",
            font=("Arial", 12, "bold"),
            height=36,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=(0, 12), pady=10, fill="x", expand=True)

        log_frame = ctk.CTkFrame(main_frame, fg_color="gray25")
        log_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(log_frame, text="Activity Log", font=("Arial", 13, "bold")).pack(
            anchor="w", padx=12, pady=(10, 6)
        )

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Courier", 9),
            bg="#0d0d0d",
            fg="#9fff9f",
            insertbackground="white",
            state="disabled",
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.bills_tree.bind("<Double-1>", self.on_tree_double_click)
        self.log_message("Application started. Ready for use.")

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
            handler = DataHandler(file_path, country_code=self.country_map.get(self.country_var.get(), "+91"))
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
                    "PHONE_NUMBER": lambda x: x.dropna().iloc[0] if len(x.dropna()) > 0 else None,
                }
            ).reset_index()

            for idx, row in party_summary.iterrows():
                party = row["Party"]
                phone = row["PHONE_NUMBER"] or "Not found"
                self.bills_tree.insert(
                    "",
                    "end",
                    iid=f"party_{idx}",
                    values=(
                        party,
                        row["BILLNO"],
                        f"Rs.{row['BALAMT']:.2f}",
                        f"{int(row['DAYS'])} days",
                        phone,
                    ),
                )
                self.party_phone_map[party] = {"original": phone, "current": phone}

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
        current_phone = values[4]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit Phone for {party_name}")
        dialog.geometry("420x210")

        ctk.CTkLabel(dialog, text=f"Party: {party_name}", font=("Arial", 11, "bold")).pack(padx=12, pady=10)
        ctk.CTkLabel(
            dialog,
            text="Enter 10-digit phone number (country code will be added):",
            font=("Arial", 10),
        ).pack(padx=12, pady=(0, 8))

        display_phone = ""
        if current_phone and current_phone != "Not found" and str(current_phone).startswith("+"):
            cc = self.country_map.get(self.country_var.get(), "+91")
            display_phone = str(current_phone)[len(cc):]

        phone_entry = ctk.CTkEntry(dialog, font=("Arial", 12), placeholder_text="10 digits only")
        phone_entry.pack(padx=12, pady=6, fill="x")
        phone_entry.insert(0, display_phone)

        def save_phone():
            new_phone_raw = phone_entry.get().strip()
            if not (new_phone_raw.isdigit() and len(new_phone_raw) == 10):
                messagebox.showerror("Error", "Please enter exactly 10 digits")
                return

            cc = self.country_map.get(self.country_var.get(), "+91")
            new_phone = f"{cc}{new_phone_raw}"
            values[4] = new_phone
            self.bills_tree.item(item, values=values)

            self.party_phone_map[party_name]["current"] = new_phone
            if self.current_bills_data is not None:
                self.current_bills_data.loc[self.current_bills_data["Party"] == party_name, "PHONE_NUMBER"] = new_phone

            self.log_message(f"OK: Updated phone for {party_name}: {new_phone}")
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save", command=save_phone).pack(padx=12, pady=10, fill="x")
        phone_entry.focus()

    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"\n{message}")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start_sending(self):
        if self.running:
            messagebox.showwarning("Warning", "Process already running")
            return
        if not self.selected_file.get():
            messagebox.showerror("Error", "Please select an Excel/CSV file first")
            return

        try:
            min_days = int(self.days_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Minimum Days must be a valid number")
            return

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

        country_code = self.country_map.get(self.country_var.get(), "+91")
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
                    "PHONE_NUMBER": "first",
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
                        message = message.replace(f"{{{col}}}", str(row[col]))

                    party = row.get("Party", "Customer")
                    phone = row.get("PHONE_NUMBER", "")

                    if not phone:
                        self.log_message(f"\nWARNING: Skipping {party}: No valid 10-digit phone number")
                        failed_count += 1
                        continue

                    if phone in sent_phones:
                        self.log_message(f"\nWARNING: Skipping duplicate phone for {party}: {phone}")
                        continue

                    self.log_message(f"\nSending to: {party} ({row.get('DAYS', '?')} days)")
                    self.log_message(f" Message: {message[:70]}...")

                    bot.send_message(phone, message)

                    self.log_message("OK: Message sent successfully")
                    success_count += 1
                    sent_phones.add(phone)
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

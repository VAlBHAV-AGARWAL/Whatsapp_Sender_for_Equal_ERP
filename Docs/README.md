# WhatsApp Message OS - Desktop Automation Tool

**A standalone Windows desktop application for automating WhatsApp reminders for outstanding bills.**

---

## 📋 Table of Contents

1. [Features](#features)
2. [System Requirements](#system-requirements)
3. [Installation from Source](#installation-from-source)
4. [Building the Executable](#building-the-executable)
5. [Usage Guide](#usage-guide)
6. [Project Structure](#project-structure)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Modern GUI** with dark/light mode built on CustomTkinter
- **Intelligent Excel/CSV Parsing** that handles messy, visually-formatted accounting exports
- **Automatic Party Name Extraction** using forward-fill logic for grouped bill rows
- **Phone Number Validation** with automatic country code formatting
- **Days Threshold Filtering** to target overdue bills only
- **Selenium-Based WhatsApp Automation** via WhatsApp Web
- **Persistent Login** - scan QR code once, reuse login for future sessions
- **Anti-Ban Protection** with randomized delays (15-35 seconds) between messages
- **Real-time Activity Log** showing send progress and any errors
- **Standalone .exe** Packaging with PyInstaller

---

## 🖥️ System Requirements

- **OS:** Windows 10 or later
- **Python:** Python 3.8+ (for development/running from source)
- **RAM:** Minimum 4GB (8GB+ recommended)
- **Internet:** Active internet connection required
- **WhatsApp Account:** Personal WhatsApp account set up on WhatsApp Web
- **Browser:** Chrome (installed system-wide)

---

## 🚀 Installation from Source

### Step 1: Clone/Download Project

```bash
cd d:\Vaibhav\Codes\whatsapp message OS software
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application

```powershell
python main.py
```

---

## 🔨 Building the Executable (.exe)

### Option 1: Using the Spec File (Recommended)

```powershell
# Activate venv (if not already activated)
.\venv\Scripts\Activate.ps1

# Build using spec file
pyinstaller WhatsApp_Message_OS.spec

# Find the executable in:
# - dist\WhatsApp_Message_OS\WhatsApp_Message_OS.exe  (single folder distribution)
# OR
# - dist\WhatsApp_Message_OS.exe  (if not using COLLECT)
```

### Option 2: Direct PyInstaller Command

```powershell
pyinstaller --name="WhatsApp_Message_OS" ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "config.json:." ^
    --hidden-import=customtkinter ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    --onefile ^
    main.py
```

### Build Output

- **Single File:** `dist\WhatsApp_Message_OS.exe` (requires `--onefile`, ~500MB)
- **Directory Distribution:** `dist\WhatsApp_Message_OS\` folder with exe and dependencies

### Tip for Distribution

For smaller file size and faster startup, use the directory distribution (without `--onefile`):
```powershell
# Creates dist\WhatsApp_Message_OS\ folder
pyinstaller WhatsApp_Message_OS.spec
```

---

## 📖 Usage Guide

### First-Time Setup

1. **Launch Application**
   - Run `WhatsApp_Message_OS.exe` or `python main.py`
   - A modern dark-themed window will open

2. **Log In to WhatsApp Web**
   - On first run, a Chrome browser window will open showing WhatsApp Web
   - Scan the QR code with your phone
   - **The login is persistent** - you won't need to scan every time!

3. **Select Your Excel/CSV Report**
   - Click "Browse File" button
   - Select your accounting software's exported Excel or CSV file
   - The app will automatically detect and parse the data

### Sending Messages

4. **Set Parameters**
   - Enter **Minimum Days Outstanding** (e.g., 60 = send to bills overdue 60+ days)
   - Edit the **Message Template** using variables:
     - `{Party}` - Customer name
     - `{BILLNO}` - Bill number
     - `{BALAMT}` - Balance amount
     - `{DAYS}` - Days outstanding

   Example template:
   ```
   Hi {Party}, 

   We noticed your bill {BILLNO} (₹{BALAMT}) has been pending for {DAYS} days. 
   Could you please arrange payment at your earliest convenience?

   Thank you!
   ```

5. **Save Template**
   - Click "Save Template" to store your message for future use

6. **Start Sending**
   - Click "START SENDING" (green button)
   - The app will:
     - Parse and validate all bills
     - Filter by your Days threshold
     - Send messages one by one
     - Wait 15-35 seconds automatically between each (anti-ban safety)
     - Log all activity to the bottom panel

7. **Monitor Progress**
   - Watch the Activity Log for:
     - Number of matching bills found
     - Individual message send confirmations
     - Any errors encountered
     - Final summary with success count

---

## 📁 Project Structure

```
whatsapp message OS software/
├── main.py                      # Entry point & GUI (CustomTkinter)
├── data_handler.py              # Excel/CSV parsing logic
├── whatsapp_bot.py              # Selenium WhatsApp automation
├── config.json                  # User settings & templates
├── requirements.txt             # Python dependencies
├── WhatsApp_Message_OS.spec     # PyInstaller configuration
├── dist/                        # Build output folder (after PyInstaller)
│   └── WhatsApp_Message_OS/     # Packaged application
│       └── WhatsApp_Message_OS.exe
└── build/                       # PyInstaller build artifacts
```

### Key Files Explained

| File | Purpose |
|------|---------|
| `main.py` | CustomTkinter GUI, file selection, message template editor, activity logging |
| `data_handler.py` | Parses messy Excel, finds headers, extracts party names, cleans phone numbers |
| `whatsapp_bot.py` | Selenium WebDriver automation, persistent Chrome profile, message sending |
| `config.json` | Stores last file path, min days, message template, country code |
| `WhatsApp_Message_OS.spec` | PyInstaller configuration for .exe creation |

---

## ⚙️ Configuration

### config.json

The application automatically creates `config.json` in the working directory:

```json
{
    "last_file": "C:\\path\\to\\your\\export.xlsx",
    "min_days": 60,
    "message_template": "Hi {Party}, Your bill...",
    "country_code": "+91"
}
```

**Modifiable fields:**
- `last_file` - Remember your last selected file
- `min_days` - Default days threshold
- `message_template` - Your default message
- `country_code` - For phone number formatting (e.g., "+91" for India)

### Chrome Profile

The app stores WhatsApp Web session data in:
```
C:\Users\[YourUsername]\AppData\Local\WhatsAppBot\Chrome\
```

This ensures your login persists across sessions.

---

## 🐛 Troubleshooting

### Issue 1: "QR code still visible - please scan"

**Solution:**
- The browser window is waiting for you to scan the QR code
- Open the displayed Chrome window and scan with your phone
- After scanning, return to the app and wait for it to load

### Issue 2: "DAYS column not found"

**Solution:**
- Ensure your Excel file has the required headers:
  - `DATE`, `BILLNO`, `AGENT`, `DAYS`, `NETAMT`, `BALAMT`, `HASTE`, `PHONE`, `MOBILE`
- The app automatically finds headers starting from row 5
- If headers are in a different row, check your export settings

### Issue 3: "No bills found with >= X days outstanding"

**Solution:**
- Check that your Excel file actually contains bills meeting the threshold
- Verify the `DAYS` column contains numeric values
- Reduce the `min_days` value to test with older bills

### Issue 4: "Phone numbers not cleaning properly"

**Solution:**
- Ensure phone numbers are in `PHONE` or `MOBILE` columns
- Check that numbers contain at least 10 digits
- Verify country code in `config.json` is correct for your region

### Issue 5: "send button not found" or timeout errors

**Solution:**
- **Network Issue:** Your internet may be slow. The app has a 15-second wait timeout.
- **Rate Limited:** WhatsApp may have temporarily blocked automated sends. Wait 24 hours.
- **Multiple Logins:** Try logging out from WhatsApp Web (in the Chrome window) and scanning the QR code again
- **Chrome Issue:** Reinstall Chrome or clear the WhatsApp profile:
  ```powershell
  Remove-Item -Path "$env:APPDATA\..\Local\WhatsAppBot\" -Recurse -Force
  ```

### Issue 6: .exe fails to run after building

**Solution:**
- Ensure all dependencies are in `requirements.txt`
- Try rebuilding with:
  ```powershell
  pyinstaller --clean WhatsApp_Message_OS.spec
  ```
- Check that Python 3.8+ is installed (verify with `python --version`)

---

## 🔐 Privacy & Security Notes

- **No Data Transmission:** This tool keeps all data local. Message templates and file data never leave your computer.
- **Persistent Login:** Your WhatsApp Web login is stored locally in Chrome profile (`AppData\Local\WhatsAppBot\`).
- **Phone Numbers:** Phone numbers are extracted from your Excel file and only used to construct WhatsApp URLs - not transmitted externally.
- **Message Content:** All messages are sent directly from your WhatsApp account through your browser.

---

## 📝 Example Excel File Format

The app expects files exported from accounting software in this format:

```
Firm Name / Report Header (Row 1-4): Ignored by app

DATE       | BILLNO  | AGENT   | DAYS | NETAMT | BALAMT | HASTE | PHONE      | MOBILE
-----------|---------|---------|------|--------|--------|-------|------------|----------
Party : ABC Enterprises Ltd.
2024-01-15 | INV001  | Agent A | 62   | 50000  | 50000  | N/A   | 9876543210 | 
2024-01-16 | INV002  | Agent B | 58   | 30000  | 30000  | N/A   | 9876543211 |
Party : XYZ Corporation
2024-01-20 | INV003  | Agent A | 45   | 25000  | 25000  | N/A   |            | 9876543212
```

The app will:
1. ✓ Skip rows 1-4 (firm header)
2. ✓ Find the header row with column names
3. ✓ Extract "ABC Enterprises Ltd." and "XYZ Corporation" as Party names
4. ✓ Assign parties to their bills automatically
5. ✓ Clean phone numbers and apply country code
6. ✓ Filter and send accordingly

---

## 🤝 Support & Contribution

For issues or improvements, ensure:
- Your Excel file matches the expected format
- Python 3.8+ is installed
- Chrome browser is installed system-wide
- All dependencies in `requirements.txt` are installed

---

## 📜 License

This tool is provided as-is for personal use. Ensure compliance with WhatsApp's Terms of Service when using automated messaging.

---

**Happy automating! 🚀**

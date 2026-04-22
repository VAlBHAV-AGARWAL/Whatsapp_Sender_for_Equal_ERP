# 📱 WhatsApp Bulk Messenger Pro

**Professional bulk messaging solution for businesses** - Send automated WhatsApp payment reminders from ERP-exported Excel/CSV files with enterprise-grade reliability.

## ✨ Key Features

- 🎯 **Smart Phone Detection** - Automatically extracts mobile & phone numbers from Excel/CSV
- 🔗 **WhatsApp Web Integration** - Seamless connection with validation
- 📊 **Real-time Preview** - Visual data preview with editable phone numbers
- 🎨 **Modern UI** - Professional dark theme with intuitive controls
- 📋 **Activity Logging** - Detailed logs for all operations
- 🛡️ **Safe & Reliable** - Built-in delays and error handling

## 🚀 Quick Start

```powershell
# 1) Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run application
python main.py
```

## 📋 Requirements

- Python 3.8+
- Windows 10/11
- WhatsApp Web compatible browser
- Excel/CSV files with party and billing data
- Excel/CSV parsing for ERP-style reports
- Party extraction from `Party :` rows
- Phone cleaning and country code support
- One message per party (deduplicated)
- `STOP SENDING` button for safe interruption
- Safer pacing:
  - random delay between sends: 25-45 seconds
  - cooling break every 20-30 sends: 5-10 minutes
- `pywhatkit` based sending (no Selenium)

## Project Structure

```text
whatsapp message OS software/
|-- main.py
|-- data_handler.py
|-- whatsapp_bot.py
|-- requirements.txt
|-- WhatsApp_Message_OS.spec
|-- Docs/
|-- run.bat
`-- build.ps1
```

## How Sending Works

1. Load your ERP export (`.xls`, `.xlsx`, `.csv`)
2. App extracts party, bill number, days, amount, phone
3. Filter by Min Days
4. Group by party and send one consolidated reminder per party
5. Use cooldown delays to reduce burst behavior

## Important Privacy Notes

This project is configured to avoid pushing sensitive local data.

Ignored by default in `.gitignore`:

- `config.json`
- `PyWhatKit_DB.txt`
- `*.xls`, `*.xlsx`, `*.csv`

If these files were already committed in an older history, remove them from git history before sharing publicly.

## Build EXE

```powershell
pyinstaller WhatsApp_Message_OS.spec
```

## Documentation

- Main guide: `Docs/README.md`
- Setup/build: `Docs/SETUP_INSTRUCTIONS.md`
- Excel format: `Docs/EXCEL_FORMAT_GUIDE.md`
- Quick reference: `Docs/QUICK_REFERENCE.md`

## Disclaimer

Use responsibly and follow WhatsApp policies and local regulations. Send only to customers with valid business context/consent.

# WhatsApp Message OS 
## Automated WhatsApp Reminder System for Outstanding Bills

**A complete, production-ready Windows desktop utility for sending customized WhatsApp reminders to customers with outstanding bills.**

---

## 🚀 Quick Start (3 Steps)

```powershell
# Step 1: Activate virtual environment
.\venv\Scripts\Activate.ps1

# Step 2: Install dependencies (already done!)
pip install -r requirements.txt

# Step 3: Run the application
python main.py
```

**That's it!** The GUI will guide you through the rest.

---

## 📁 Project Structure

```
whatsapp-message-os/
├── 📄 Core Application Files
│   ├── main.py                      # GUI application
│   ├── data_handler.py              # Excel parsing logic
│   ├── whatsapp_bot.py              # Selenium automation
│   └── config.json                  # Settings (auto-created)
│
├── 🔧 Build & Configuration
│   ├── requirements.txt             # Python dependencies ✅ INSTALLED
│   ├── WhatsApp_Message_OS.spec     # PyInstaller config
│   ├── run.bat                      # Quick launcher
│   └── build.ps1                    # Build automation
│
├── 📚 Documentation (in Docs/ folder)
│   ├── INDEX.md                     # 👈 START HERE!
│   ├── README.md                    # Complete user guide
│   ├── SETUP_INSTRUCTIONS.md        # Installation & build
│   ├── EXCEL_FORMAT_GUIDE.md        # File format specs
│   ├── QUICK_REFERENCE.md           # Command cheat sheet
│   ├── PROJECT_SUMMARY.md           # Technical overview
│   └── DELIVERY_COMPLETE.md         # Deliverables verification
│
└── venv/                            # Virtual environment ✅ ACTIVE
```

---

## 📖 Documentation

**All documentation has been moved to the [Docs/](Docs/) folder for better organization!**

### Where to Start:

- **👤 First-time user?** → [Docs/INDEX.md](Docs/INDEX.md) ⭐ START HERE
- **⚡ Want quick commands?** → [Docs/QUICK_REFERENCE.md](Docs/QUICK_REFERENCE.md)
- **📊 Need setup help?** → [Docs/SETUP_INSTRUCTIONS.md](Docs/SETUP_INSTRUCTIONS.md)
- **📋 Need file format info?** → [Docs/EXCEL_FORMAT_GUIDE.md](Docs/EXCEL_FORMAT_GUIDE.md)
- **👨‍💻 Developer/architect?** → [Docs/PROJECT_SUMMARY.md](Docs/PROJECT_SUMMARY.md)

---

## ✨ Key Features

✅ **Intelligent Excel Parsing** - Handles messy accounting software exports  
✅ **Party Extraction** - Automatically extracts customer names from "Party :" rows  
✅ **Phone Cleaning** - Validates & normalizes phone numbers  
✅ **WhatsApp Automation** - Selenium-based with persistent login  
✅ **Anti-Ban Protection** - Random 15-35 second delays between messages  
✅ **Professional GUI** - Modern dark/light CustomTkinter interface  
✅ **Standalone .exe** - Build and distribute as single executable  
✅ **Configuration Storage** - Save templates and settings locally  

---

## 🎯 What It Does

1. **Parse Excel/CSV** - From your accounting software
2. **Extract Customer Names** - Automatically from "Party :" rows
3. **Filter Bills** - By outstanding days threshold
4. **Clean Phone Numbers** - Validate and add country codes
5. **Send WhatsApp** - Customized messages via Selenium
6. **Log Progress** - Real-time activity updates

---

## 💻 System Requirements

- **OS:** Windows 10 or later
- **Python:** 3.8+ (already installed! ✅)
- **Chrome:** Must be installed system-wide
- **Internet:** Active internet connection
- **WhatsApp:** Active WhatsApp account

---

## 🛠️ Useful Commands

| Command | Purpose |
|---------|---------|
| `python main.py` | Launch the application |
| `.\run.bat` | Quick launcher (no PowerShell needed) |
| `pyinstaller WhatsApp_Message_OS.spec` | Build .exe |
| `pip install -r requirements.txt` | Install dependencies |

---

## ⚡ Next Steps

1. **Read [Docs/INDEX.md](Docs/INDEX.md)** - Choose your path (2 min)
2. **Launch the app** - `python main.py`
3. **Prepare Excel file** - Check [Docs/EXCEL_FORMAT_GUIDE.md](Docs/EXCEL_FORMAT_GUIDE.md)
4. **Send test messages** - Start with 1-2 bills
5. **Build .exe** (optional) - See [Docs/SETUP_INSTRUCTIONS.md](Docs/SETUP_INSTRUCTIONS.md)

---

## 📞 Documentation Map

```
Docs/
├── INDEX.md ⭐ START HERE - Navigation and path selection
├── README.md - Full user guide with features
├── SETUP_INSTRUCTIONS.md - Installation and build steps
├── EXCEL_FORMAT_GUIDE.md - File format requirements
├── QUICK_REFERENCE.md - Commands and tips
├── PROJECT_SUMMARY.md - Technical architecture
└── DELIVERY_COMPLETE.md - Deliverables verification
```

---

## 🔐 Security & Privacy

✅ **All local** - No cloud uploads or external APIs  
✅ **Your data** - Everything stays on your computer  
✅ **Direct sending** - Messages go directly from your WhatsApp  
✅ **Persistent login** - QR code scan once, reuse forever  

---

## 🚀 Ready to Start?

```powershell
# Everything is already set up! Just run:
python main.py
```

Then open [Docs/INDEX.md](Docs/INDEX.md) for detailed guidance!

---

**Status:** ✅ **PRODUCTION READY**  
**Dependencies:** ✅ **INSTALLED**  
**Documentation:** ✅ **COMPLETE**  

🎉 **You're all set to send WhatsApp reminders!**

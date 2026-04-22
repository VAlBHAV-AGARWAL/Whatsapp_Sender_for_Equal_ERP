# 🎯 WhatsApp Message OS - Quick Reference Card

**Laminate this or save as your desktop wallpaper background for quick access!**

---

## ⚡ Quick Start Commands

### First Time Setup
```powershell
cd "d:\Vaibhav\Codes\whatsapp message OS software"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Run Application (Daily Use)
```powershell
cd "d:\Vaibhav\Codes\whatsapp message OS software"
.\venv\Scripts\Activate.ps1
python main.py

# OR simply double-click:
# ► run.bat
```

### Build Standalone .exe
```powershell
cd "d:\Vaibhav\Codes\whatsapp message OS software"
.\venv\Scripts\Activate.ps1

# Option 1: Interactive build script
powershell -ExecutionPolicy Bypass -File build.ps1

# Option 2: Direct command
pyinstaller WhatsApp_Message_OS.spec
```

---

## 📂 Project Files

| File | Purpose |
|------|---------|
| `main.py` | GUI + orchestration |
| `data_handler.py` | Excel parsing |
| `whatsapp_bot.py` | Selenium automation |
| `config.json` | Settings (auto-created) |
| `requirements.txt` | Dependencies |
| `WhatsApp_Message_OS.spec` | PyInstaller config |

---

## 📋 Expected Excel Format

```
ROWS 1-4:     [Firm Header - Ignored]
ROW 5:        DATE | BILLNO | AGENT | DAYS | NETAMT | BALAMT | HASTE | PHONE | MOBILE
ROW 6:        Party : ABC Company
ROWS 7-9:     [Bills for ABC Company]
ROW 10:       Party : XYZ Company
ROWS 11-13:   [Bills for XYZ Company]
```

**Critical:** "Party :" rows mark customer groups - app auto-assigns names to bills!

---

## 💬 Message Template Variables

| Variable | Example | Used For |
|----------|---------|----------|
| `{Party}` | ABC Company Ltd. | Customer name |
| `{BILLNO}` | INV-2024-001 | Invoice/bill number |
| `{BALAMT}` | 50000.00 | Outstanding balance |
| `{DAYS}` | 62 | Days outstanding |

**Example Template:**
```
Hi {Party}, Your bill {BILLNO} 
(₹{BALAMT}) is pending for {DAYS} days. 
Please arrange payment. Thank you!
```

---

## 📱 Phone Number Processing

| Input | Output (+91) |
|-------|--------------|
| 9876543210 | +919876543210 |
| +919876543210 | +919876543210 |
| 09876543210 | +919876543210 |
| 98 7654 3210 | +919876543210 |

**Rule:** Strips non-digits, keeps last 10, adds country code

---

## 🛠️ Configuration (config.json)

```json
{
    "last_file": "path/to/your/export.xlsx",
    "min_days": 60,
    "message_template": "Hi {Party}...",
    "country_code": "+91"
}
```

**Auto-updated when:**
- You click "Save Template"
- App closes normally
- New file selected

---

## ⚙️ Default Settings

| Setting | Default | Where to Change |
|---------|---------|-----------------|
| Min Days | 60 | GUI input box |
| Country Code | +91 | config.json |
| Message | See below | GUI text editor |
| Theme | Dark | `main.py` line 24 |

**Default Template:**
```
Hi {Party}, Your bill {BILLNO} of amount ₹{BALAMT} 
is pending for {DAYS} days. 
Please arrange payment at your earliest.
```

---

## 🚀 Step-by-Step: Send Your First Messages

1. **Prepare Excel File**
   - Export from accounting software
   - Verify format (see above)
   - Save as .xlsx or CSV

2. **Launch App**
   - Run `python main.py` or double-click `run.bat`
   - GUI window opens

3. **Select File**
   - Click "Browse File" button
   - Choose your Excel file
   - App shows file name

4. **Set Threshold**
   - Enter minimum days (e.g., 60)
   - This filters bills

5. **Customize Message**
   - Edit the template text box
   - Use {Party}, {BILLNO}, {BALAMT}, {DAYS}
   - Preview in message editor

6. **Save Settings**
   - Click "Save Template"
   - Settings saved to config.json

7. **Start Sending**
   - Click "START SENDING" (green button)
   - Monitor activity log
   - App handles delays automatically

8. **Verify**
   - Check activity log for success count
   - Verify customers received messages on WhatsApp

---

## 🔐 First-Time WhatsApp Login

1. **App opens Chrome window**
   - Shows WhatsApp Web
   - Displays QR code

2. **Scan QR Code**
   - Open WhatsApp on your phone
   - Settings > Linked Devices > Link a Device
   - Scan the QR code

3. **Wait for Loading**
   - App waits ~2 minutes for login
   - Don't close Chrome window

4. **Login Persistent**
   - ✅ You only scan ONCE
   - Future runs remember your login
   - Stored in Chrome profile

---

## ⏱️ Timing & Anti-Ban Protection

- **Delay between messages:** Random 15-35 seconds
- **Why?** Prevents WhatsApp rate limiting/blocking
- **Adjustable?** Yes, modify `whatsapp_bot.py` line ~195
- **Example:** 5 bills = 1-2 minutes total

---

## 🐛 Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| "No module named customtkinter" | `pip install -r requirements.txt` |
| Chrome not opening | Install Chrome system-wide |
| "No bills found" | Lower min_days value OR check Excel format |
| Slow message sending | Network issue - wait or reduce bill count |
| QR code not scanning | Delete `%APPDATA%/..\Local\WhatsAppBot` folder |
| .exe won't run | Reinstall Python or rebuild with `pyinstaller WhatsApp_Message_OS.spec` |

---

## 📁 Folder Structure After Setup

```
whatsapp-message-os/
├── main.py [✓]
├── data_handler.py [✓]
├── whatsapp_bot.py [✓]
├── config.json [✓]
├── requirements.txt [✓]
├── venv/ [← Created after setup]
├── dist/ [← Created after build]
└── build/ [← Created after build]
```

---

## 🎯 Feature Checklist

**Data Parsing:**
- ✅ Skips junk header rows
- ✅ Finds headers dynamically
- ✅ Extracts "Party :" names
- ✅ Assigns parties to bills
- ✅ Cleans phone numbers
- ✅ Filters by days threshold

**GUI:**
- ✅ Modern dark interface
- ✅ File browser
- ✅ Message template editor
- ✅ Activity log
- ✅ Settings persistence

**WhatsApp Automation:**
- ✅ Selenium WebDriver
- ✅ QR code login (one-time)
- ✅ Persistent session
- ✅ URL-based sending
- ✅ Anti-ban delays (15-35s)
- ✅ Error handling

**Deployment:**
- ✅ Standalone .exe
- ✅ No Python required (for .exe)
- ✅ Portable
- ✅ Single-click launch

---

## 📞 When Things Don't Work

### Before Asking for Help:

1. **Check log messages** in Activity Log (bottom box)
2. **Verify Excel file** using EXCEL_FORMAT_GUIDE.md
3. **Try small batch** (e.g., 1-2 bills first)
4. **Check internet** and Chrome installation
5. **Search SETUP_INSTRUCTIONS.md** for issue

### Information Needed for Help:

```
1. Exact error message: _______________
2. What step fails: _______________
3. Excel file format: □ .xlsx  □ .csv
4. Python version: _______________
5. Windows version: _______________
```

---

## 💡 Pro Tips

1. **Template Variables:** Use all 4 for complete message
2. **Test First:** Always test with 1-2 bills before bulk send
3. **Save Template:** After every customization
4. **Monitor Log:** Watch activity log for issues
5. **Delays:** 15-35 seconds per message keeps you safe
6. **Phone Format:** Ensure 10 digits (+country code will be added)
7. **Party Names:** Excel must have "Party :" rows
8. **Re-login:** If messages fail, maybe WhatsApp logged out

---

## 🚀 Performance Expectations

| Operation | Time |
|-----------|------|
| File parsing | 5-10 seconds |
| First WhatsApp load | 10-15 seconds |
| Per message | 15-35 seconds (auto delay) |
| 100 messages | 25-60 minutes |
| Build .exe | 2-5 minutes |

---

## 🔗 File Links (In Workspace)

- **[README.md](README.md)** - Full user guide
- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Installation guide
- **[EXCEL_FORMAT_GUIDE.md](EXCEL_FORMAT_GUIDE.md)** - File format specs
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview

---

## ✅ Use Cases

✓ Automated AR (Accounts Receivable) reminders  
✓ Overdue invoice notifications  
✓ Payment due reminders  
✓ Customer follow-ups  
✓ Bulk messaging campaigns  
✓ Status updates to multiple parties  

---

## ⚠️ Important Notes

- **Legal:** Comply with WhatsApp ToS for automated messaging
- **Data:** All data stays local - nothing uploaded
- **Privacy:** Phone numbers only used for WhatsApp URLs
- **Security:** Login stored only in local Chrome profile
- **Rate Limit:** 15-35s delays help avoid WhatsApp blocks

---

## 🎓 For Developers

**To modify:**

```python
# Change country code:
# config.json → "country_code": "+44"

# Change theme:
# main.py → ctk.set_appearance_mode("light")

# Change delays:
# whatsapp_bot.py → randint(20, 40) instead of (15, 35)

# Add filters:
# data_handler.py → def filter_by_custom_logic()
```

See source code comments for more details.

---

## 📱 Example Single Message Flow

```
User selects: export.xlsx
User sets: min_days = 60
User enters template: "Hi {Party}, Bill {BILLNO} pending for {DAYS} days"

↓↓↓ APP PROCESSES ↓↓↓

Bill Row → Extract: Party="ABC Ltd", BILLNO="INV001", DAYS=62, PHONE="9876543210"
Filter: DAYS(62) >= min_days(60) ✓ PASS
Phone Cleaned: "9876543210" → "+919876543210"
Template → "Hi ABC Ltd, Bill INV001 pending for 62 days"
URL Encoded + Sent via WhatsApp Web
Wait 23 seconds (random 15-35)
→ Next bill...

↑↑↑ FINAL RESULT ↑↑↑

Activity Log: "✅ Sent to ABC Ltd: Bill INV001 (₹50000, 62 days)"
Message appears in WhatsApp: "Hi ABC Ltd, Bill INV001 pending for 62 days"
```

---

**Print this page and keep it handy!** 📋

**Questions?** Check README.md or SETUP_INSTRUCTIONS.md

**Ready to go?** Run: `python main.py` 🚀

# 🔧 Setup & Build Instructions - WhatsApp Message OS

Complete step-by-step guide to get the application running from source and build the standalone .exe.

---

## 📋 Pre-Requirements Check

Before starting, verify you have:

```powershell
# Check Python version (should be 3.8 or higher)
python --version

# Check pip is available
pip --version

# Check Chrome is installed (should open a browser)
chrome
```

If any command fails, install the missing software first.

---

## 🎯 Step 1: Development Setup (For Running from Source)

### 1.1 Navigate to Project Folder

```powershell
cd "d:\Vaibhav\Codes\whatsapp message OS software"
```

### 1.2 Create Virtual Environment

```powershell
# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# For PowerShell:
.\venv\Scripts\Activate.ps1

# For Command Prompt (cmd.exe):
# .\venv\Scripts\activate.bat

# Verify activation (prompt should show (venv) prefix)
```

### 1.3 Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 1.4 Install Dependencies

```powershell
pip install -r requirements.txt
```

**This installs:**
- `customtkinter` - Modern GUI framework
- `pandas` - Excel/CSV data processing
- `openpyxl` - Excel file support
- `selenium` - Browser automation
- `webdriver-manager` - Automatic ChromeDriver management
- `pyinstaller` - Executable packaging

### 1.5 Test Run the Application

```powershell
python main.py
```

**Your first run will:**
1. Open a GUI window
2. Open a Chrome browser for WhatsApp Web
3. Display a QR code for you to scan
4. After scanning, the app is ready to use

✓ **If this works, development setup is complete!**

---

## 📦 Step 2: Building the Executable (.exe)

### Option A: Build Using Spec File (Recommended)

This is the cleanest approach with minimal file size.

```powershell
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Build using the .spec file
pyinstaller WhatsApp_Message_OS.spec

# Build output will be in: dist\WhatsApp_Message_OS\
```

**Output structure:**
```
dist/
└── WhatsApp_Message_OS/
    ├── WhatsApp_Message_OS.exe
    ├── config.json
    ├── _internal/
    │   ├── (all Python dependencies)
    │   └── (chrome driver, pandas, etc.)
    └── (other support files)
```

### Option B: Build as Single File (Larger, But Portable)

If you want a single .exe file instead of a folder:

```powershell
pyinstaller --name="WhatsApp_Message_OS" ^
    --windowed ^
    --onefile ^
    --add-data "config.json:." ^
    --hidden-import=customtkinter ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=selenium ^
    --hidden-import=webdriver_manager ^
    main.py
```

**Output:** `dist\WhatsApp_Message_OS.exe` (single file, ~500MB)

---

## ✅ Step 3: Test the Built Executable

### 3.1 First Test - From Build Directory

```powershell
# Navigate to build output
cd dist\WhatsApp_Message_OS

# Run the executable
.\WhatsApp_Message_OS.exe
```

### 3.2 Verify Functionality

1. **GUI appears** - Modern dark interface loads
2. **Browser opens** - Chrome window for WhatsApp Web
3. **QR code displays** - Scan with your phone
4. **Application ready** - File browser and controls are accessible

✓ **If this works, the build is successful!**

---

## 🚀 Step 4: Distribute the Application

### For Small Distribution (Folder)

```powershell
# Copy the entire dist\WhatsApp_Message_OS\ folder
# Example:
xcopy "dist\WhatsApp_Message_OS" "C:\Program Files\WhatsApp Message OS" /E /I

# Create a shortcut to WhatsApp_Message_OS.exe for the desktop
```

### Create Desktop Shortcut (Windows)

1. Navigate to `dist\WhatsApp_Message_OS\`
2. Right-click `WhatsApp_Message_OS.exe`
3. Select "Create shortcut"
4. Move shortcut to Desktop

Or via PowerShell:

```powershell
$SourceFileLocation = "dist\WhatsApp_Message_OS\WhatsApp_Message_OS.exe"
$ShortcutLocation = "WhatsApp_Message_OS.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutLocation)
$Shortcut.TargetPath = (Resolve-Path $SourceFileLocation)
$Shortcut.Save()

# Move to Desktop
Move-Item $ShortcutLocation ([Environment]::GetFolderPath("Desktop"))
```

---

## 🔄 Step 5: Clean Rebuild (If Issues Arise)

Sometimes old build artifacts cause issues. Clean rebuild:

```powershell
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Remove old build artifacts
Remove-Item -Path build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "WhatsApp_Message_OS.egg-info" -Recurse -Force -ErrorAction SilentlyContinue

# Clean build
pyinstaller --clean WhatsApp_Message_OS.spec
```

---

## 📋 Common Build Commands Reference

### Standard Build (Folder Distribution)
```powershell
.\venv\Scripts\Activate.ps1
pyinstaller WhatsApp_Message_OS.spec
```

### Single File Build
```powershell
.\venv\Scripts\Activate.ps1
pyinstaller --onefile WhatsApp_Message_OS.spec
```

### Debug Build (with console window)
```powershell
.\venv\Scripts\Activate.ps1
pyinstaller --name="WhatsApp_Message_OS" --console main.py
```

### Custom Output Directory
```powershell
.\venv\Scripts\Activate.ps1
pyinstaller --distpath "C:\Output\Folder" WhatsApp_Message_OS.spec
```

---

## 🛠️ Troubleshooting Build Issues

### Issue: "ModuleNotFoundError: No module named 'customtkinter'"

**Solution:**
```powershell
# Reactivate venv
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Rebuild
pyinstaller WhatsApp_Message_OS.spec
```

### Issue: "ChromeDriver not found (webdriver-manager error)"

**Solution:**
```powershell
# Reinstall webdriver-manager
pip install --force-reinstall webdriver-manager

# This will auto-download ChromeDriver on first build
pyinstaller WhatsApp_Message_OS.spec
```

### Issue: "PyInstaller failed - spec file error"

**Solution:**
```powershell
# Regenerate spec file
pyinstaller --name="WhatsApp_Message_OS" ^
    --windowed ^
    --add-data "config.json:." ^
    main.py

# Rename generated .spec file
Rename-Item "WhatsApp_Message_OS.spec" "WhatsApp_Message_OS_auto.spec"
```

### Issue: Built .exe fails to run

**Solution:**
1. Run the debug version to see error messages:
   ```powershell
   pyinstaller --console main.py
   .\dist\main.exe
   ```
2. Check missing dependencies from console output
3. Add missing modules to `requirements.txt`
4. Rebuild

---

## 📊 Expected File Sizes

- **Development venv:** ~300-400 MB
- **dist folder (directory distribution):** ~450-550 MB
- **dist\WhatsApp_Message_OS.exe (single file):** ~450-550 MB

---

## ✨ Optimization Tips

### Reduce Build Size

```powershell
# Exclude unnecessary modules
$spec = Get-Content "WhatsApp_Message_OS.spec"
$spec = $spec -replace "excludedimports=\[\]", "excludedimports=['matplotlib', 'PIL', 'numpy', 'scipy']"
Set-Content "WhatsApp_Message_OS.spec" $spec

pyinstaller WhatsApp_Message_OS.spec
```

### Faster Startup

Use directory distribution (not single-file) for faster startup times.

---

## 🎁 Final Checklist Before Distribution

- [ ] Test built .exe on a fresh system (or VM) without Python installed
- [ ] Verify it opens WhatsApp Web properly
- [ ] Test file selection and bill filtering
- [ ] Confirm message sending works end-to-end
- [ ] Check config.json is created in the app directory
- [ ] Verify Chrome profile persists after close and reopen
- [ ] Test with a real Excel file from your accounting software

---

## 📝 Next Steps

1. **For Personal Use:** Run `python main.py` from source
2. **For Distribution:** Use `pyinstaller WhatsApp_Message_OS.spec` to build
3. **For Updates:** Modify source code and rebuild the .exe
4. **For Deployment:** Share the entire `dist\WhatsApp_Message_OS\` folder

---

## 🆘 Need Help?

If build fails:

1. **Check Python version:** `python --version` (must be 3.8+)
2. **Verify all dependencies:** `pip list`
3. **Check Chrome installed:** `where chrome` or `where chromium`
4. **Try clean rebuild:** Delete `build/` and `dist/` folders, then rebuild
5. **Review error messages:** Look for missing module names in error output

---

**Ready to build? Run:** 

```powershell
cd "d:\Vaibhav\Codes\whatsapp message OS software"
.\venv\Scripts\Activate.ps1
pyinstaller WhatsApp_Message_OS.spec
```

Then find your application in `dist\WhatsApp_Message_OS\` !

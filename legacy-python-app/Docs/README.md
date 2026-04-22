# WhatsApp Payment Reminder - User Guide

A Windows desktop app for sending payment-due reminders on WhatsApp from ERP export files.

## Contents

1. Features
2. Requirements
3. Installation
4. Usage
5. Troubleshooting
6. Privacy

## Features

- Modern CustomTkinter UI
- Supports `.xls`, `.xlsx`, `.csv`
- Extracts customer name from `Party :` rows
- Cleans and formats phone numbers
- Country code support
- Sends one consolidated message per party
- `STOP SENDING` button
- Randomized anti-burst pacing:
  - 25-45 seconds between messages
  - 5-10 minute cooling breaks after 20-30 sends
- `pywhatkit` sender (browser-based)

## Requirements

- Windows 10+
- Python 3.8+
- Internet connection
- WhatsApp account logged in to WhatsApp Web
- Default browser available

## Installation

```powershell
cd d:\Vaibhav\Codes\whatsapp message OS software
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Usage

### 1) Open file

- Click `Browse File`
- Select your ERP export (`.xls`, `.xlsx`, or `.csv`)

### 2) Review parsed data

- Preview table shows Party, Bills, Amount, Days, Phone
- Double-click Phone cell to edit missing/incorrect numbers

### 3) Configure send settings

- Set `Min Days`
- Choose country code
- Edit message template with variables:
  - `{Party}`
  - `{BILLNO}`
  - `{BALAMT}`
  - `{DAYS}`

Example:

```text
Hi {Party}, your bill {BILLNO} of amount Rs.{BALAMT} is pending for {DAYS} days. Please arrange payment.
```

### 4) Start

- Click `START SENDING`
- Watch `Activity Log`
- Use `STOP SENDING` anytime to halt gracefully

## Notes on sending behavior

- Messages are grouped per party to avoid duplicates
- If a phone is missing/invalid, that party is skipped and logged
- App uses paced delays to reduce rapid sending bursts

## Troubleshooting

### Message typed but not sent

- App now force-presses Enter after fill.
- Keep WhatsApp Web window focused while sending.
- Avoid typing/clicking on other windows during auto-send.

### No rows to send

- Lower Min Days
- Check `DAYS` values are numeric
- Ensure phones are present and valid

### File parse issues

- Ensure headers exist: `DATE`, `BILLNO`, `DAYS`, `BALAMT`, `PHONE`/`MOBILE`
- Ensure customer blocks include `Party :` rows

## Privacy

Data stays local. No cloud API is used.

Sensitive/local files are ignored in `.gitignore`:

- `config.json`
- `PyWhatKit_DB.txt`
- `*.xls`, `*.xlsx`, `*.csv`

If any sensitive file was committed earlier, clean git history before sharing.

## Build EXE

```powershell
pyinstaller WhatsApp_Message_OS.spec
```

## Policy Reminder

Use this tool only for legitimate business communication and in compliance with WhatsApp terms.

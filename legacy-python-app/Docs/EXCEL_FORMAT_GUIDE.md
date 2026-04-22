# 📊 Expected Excel File Format Guide

This document explains the exact format your accounting software export should have for WhatsApp Message OS to parse it correctly.

---

## 📑 File Format Overview

The application expects **messy, visually-formatted Excel files** typical of accounting software exports. It's designed to handle imperfect data!

---

## 🏗️ Structure Requirements

### Row 1-4: Junk Header (Ignored)
```
| Firm Name / Report Title                        |
| Address Line 1                                  |
| Report: Outstanding Bills Report                |
| Generated: 2024-03-12                           |
```

**The app skips these rows entirely.**

---

### Row 5+: Data Section

Beyond row 5, the app looks for:

1. **Header Row** with columns: `DATE`, `BILLNO`, `AGENT`, `DAYS`, `NETAMT`, `BALAMT`, `HASTE`, `PHONE`, `MOBILE`
   - The app automatically finds this row
   - Columns don't need to be in exact order
   - All 9 columns don't need to exist (at least 8 of 9 required)

2. **Party Marker Rows** (starting with "Party :")
   - Format: `Party : [Customer Name]` in the first cell
   - Example: `Party : ABC Enterprises Ltd.`
   - The app extracts the name and applies it to all following bills until the next Party marker

3. **Bill Data Rows**
   - One row per bill
   - Must have a value in `BILLNO` (bill number column)
   - Empty `BILLNO` means it's a junk/summary row (will be removed)

---

## 📋 Complete Example

### Minimal Working Example

```
+-------+--------+--------+------+--------+--------+-------+-----+----------+
| Firm Name Report (Rows 1-4 ignored by app)                              |
+-------+--------+--------+------+--------+--------+-------+-----+----------+

| DATE      | BILLNO | AGENT | DAYS | NETAMT | BALAMT | HASTE | PHONE | MOBILE |
|-----------|--------|-------|------|--------|--------|-------|-------|--------|
| Party : XYZ Corporation                                                |
| 2024-01-15| INV001 | John  | 62   | 50000  | 50000  | N/A   | 9876  | 9876543210 |
| 2024-01-16| INV002 | Jane  | 58   | 30000  | 30000  | N/A   | 9877  | 9876543211 |
|-----------|--------|-------|------|--------|--------|-------|-------|--------|
| Party : ABC Ltd.                                                       |
| 2024-01-20| INV003 | John  | 45   | 25000  | 25000  | N/A   | 9878  | 9876543212 |
| 2024-02-10| INV004 | Jane  | 32   | 15000  | 15000  | N/A   |       | 9876543213 |
|-----------|--------|-------|------|--------|--------|-------|-------|--------|
| TOTAL                                  | 120000 | 120000 |
+-------+--------+--------+------+--------+--------+-------+-----+----------+
```

### How the App Parses This:

1. ✓ **Skips rows 1-4** (report header)
2. ✓ **Finds header row** at row 5 (contains DATE, BILLNO, AGENT, etc.)
3. ✓ **Extracts Party "XYZ Corporation"** from row 6
4. ✓ **Creates bill rows 7-8** with Party = "XYZ Corporation"
5. ✓ **Extracts Party "ABC Ltd."** from row 9
6. ✓ **Creates bill rows 10-11** with Party = "ABC Ltd."
7. ✓ **Removes row 12** (TOTAL row - no BILLNO value)
8. ✓ **Result:** 4 clean bill records with parties assigned

---

## 📱 Phone Number Handling

### Input Formats Accepted

| Format | Input | Output (India +91) |
|--------|-------|-------------------|
| Local 10-digit | 9876543210 | +919876543210 |
| With +91 | +919876543210 | +919876543210 |
| With country code | 919876543210 | +919876543210 |
| With spaces/dashes | 98 7654 3210 | +919876543210 |
| 11-digit | 09876543210 | +919876543210 (removes leading 0) |

### Phone Number Rules

- **Minimum 10 digits required** (after removing non-numeric chars)
- If more than 10 digits: keeps the last 10
- Missing phone = row is skipped (cannot send message)
- Use either `PHONE` or `MOBILE` column (app uses MOBILE if available)

---

## 🔤 Party Name Extraction Logic

### Valid Party Row Formats

All of these will be recognized:

```
Party : ABC Enterprises Ltd.
PARTY : XYZ Corporation Ltd
Party: John's Business
PARTY:  Malik Traders
Party : Company (Private) Limited  [Name extracted up to first "("]
```

### How Forward-Fill Works

```
Row 1: Party : First Company
Row 2: (Bill)     ← Gets Party = "First Company"
Row 3: (Bill)     ← Gets Party = "First Company"
Row 4: Party : Second Company
Row 5: (Bill)     ← Gets Party = "Second Company"
Row 6: Party : Third Company
```

The app remembers the most recent party name and applies it forward.

---

## ⚠️ Special Cases & Junk Data

### Rows That Get Filtered Out

1. **Empty BILLNO**
   ```
   | (empty) | John  | 62   | 50000 |  ← Removed
   ```

2. **Summary/Total Rows**
   ```
   | TOTAL | | | | 500000 | 450000 |  ← Removed (no BILLNO)
   ```

3. **Subtotal Rows**
   ```
   | Subtotal for Group | | | 450000 |  ← Removed
   ```

### Data That's Tolerated

- ✓ Extra whitespace in cells
- ✓ Missing optional columns (like HASTE)
- ✓ Mixed date formats
- ✓ Column order doesn't matter
- ✓ Blank rows between bill groups

---

## 📝 Days Column

The `DAYS` column is critical for filtering.

| Format | Accepted | Output |
|--------|----------|--------|
| 62 | ✓ | 62 |
| 62.5 | ✓ | 62 (rounded down) |
| " 62 " | ✓ | 62 (whitespace trimmed) |
| "62 days" | ✓ | 62 |
| empty / invalid | ✓ | 0 (treated as 0 days) |

---

## 💰 Balance Amount Column

| Format | Accepted | Output |
|--------|----------|--------|
| 50000 | ✓ | 50000.0 |
| 50,000 | ✓ | 50000.0 |
| 50000.50 | ✓ | 50000.5 |
| ₹50,000 | ✓ | 50000.0 |
| empty | ✓ | 0.0 |

---

## 🧪 Testing Your Excel File

Before using your actual file:

1. **Export your report** from accounting software
2. **Check row 1:** Contains firm name/report title
3. **Check row 5+:** Contains invoice/bill data
4. **Check for "Party :" rows:** Between customer groups
5. **Check columns exist:** At least `BILLNO`, `DAYS`, `BALAMT`, `PHONE` or `MOBILE`

### Quick Validation Checklist

- [ ] File is .xlsx, .xls, or .csv format
- [ ] First 4 rows can be junk (firm header)
- [ ] Row 5+ has header row with column names
- [ ] Header row contains DATE, BILLNO, AGENT, DAYS, NETAMT, BALAMT, PHONE/MOBILE
- [ ] Party names start with "Party :" or "PARTY:"
- [ ] Bill rows have values in BILLNO column
- [ ] DAYS column has numeric values
- [ ] BALAMT column has numeric values
- [ ] PHONE or MOBILE column exists

---

## 🆘 Debugging Import Issues

If the app can't parse your file:

1. **Check Column Names**
   - Open Excel and verify headers are exactly: `DATE`, `BILLNO`, `AGENT`, `DAYS`, `NETAMT`, `BALAMT`, `HASTE`, `PHONE`, `MOBILE`
   - Column names must match (case-insensitive is fine)

2. **Check Party Names**
   - Ensure party marker rows start with "Party :" (case-insensitive)
   - Party name should be extracted: `Party : [NAME]` → NAME

3. **Check Phone Numbers**
   - At least one number should have 10 digits
   - Phone numbers should be in PHONE or MOBILE column

4. **Simplify Your File**
   - Create a test file with 2-3 bills from different customers
   - If test file works, issue is with your data format
   - Compare with the example above

---

## ✅ Example: Real-World Accounting Software Export

Many accounting software (Tally, QuickBooks, SAP, etc.) export similarly. Here's a realistic example:

```xlsx
M/S SMITH & ASSOCIATES
123, Business Park, City - 400001
OUTSTANDING LEDGER REPORT
Generated on: 12-Mar-2024

DATE       BILLNO    AGENT       DAYS  NETAMT    BALAMT  HASTE  PHONE       MOBILE
====================================================================
Party : Rajesh Trading Company
15-Jan-2024 TSN/001 Raj Kumar    62    50,000    50,000  N/A    40-2580100  9876543210
18-Jan-2024 TSN/002 Priya Singh  59    30,000    30,000  N/A               9876543211
22-Jan-2024 TSN/003 Raj Kumar    55    25,000    25,000  N/A    40-2580100  9876543212

Party : ABC Exports Ltd.
10-Feb-2024 ABX/045 Priya Singh  32    75,000    75,000  N/A    80-2222222  9876543213
15-Feb-2024 ABX/046 Raj Kumar    27    45,000    45,000  N/A    80-2222222  9876543214

====================================================================
REPORT TOTAL:                            225,000   225,000
```

**Expected Result:** 5 bills (2 from Rajesh Trading, 3 from ABC Exports) with phone numbers cleaned and parties assigned.

---

## 🎯 File Format Checklist

Use this before importing a new file:

```
[ ] File exists at specified path
[ ] File extension is .xlsx, .xls, or .csv
[ ] Rows 1-4 are throwaway header (optional names, addresses)
[ ] Row 5 or later contains column headers (DATE, BILLNO, etc.)
[ ] Party names formatted as: "Party : [NAME]"
[ ] Bill rows have non-empty BILLNO values
[ ] DAYS column has numeric values (not text)
[ ] BALAMT column has numeric values (not text)
[ ] PHONE or MOBILE column present with 10+ digit numbers
[ ] No merged cells (if .xlsx) - can cause parsing issues
```

---

**Ready to import your file?** Use the app's file browser and check the activity log for any parsing warnings! 🚀

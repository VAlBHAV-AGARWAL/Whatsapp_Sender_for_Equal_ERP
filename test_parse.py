#!/usr/bin/env python3
"""Test script to verify file parsing works with the sample file"""

from data_handler import DataHandler

# Test opening the sample file
handler = DataHandler("12345.xls", country_code="+91")
df = handler.parse_file()

if df is not None:
    print(f"✓ File parsed successfully!")
    print(f"\nShape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst 10 rows:")
    print(df.head(10))
    print(f"\nUnique parties: {df['Party'].nunique()}")
    print(f"Parties: {df['Party'].unique()}")
else:
    print("✗ Failed to parse file")

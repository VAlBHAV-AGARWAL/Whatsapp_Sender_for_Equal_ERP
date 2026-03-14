"""
Data Handler Module - Parsing and processing Excel/CSV reports
Handles the messy, visually-formatted accounting software exports
"""

import pandas as pd
import re
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataHandler:
    """Handle data parsing, cleaning, and filtering"""
    
    def __init__(self, file_path, country_code="+91"):
        self.file_path = file_path
        self.country_code = country_code
        
    def parse_file(self):
        """
        Parse Excel/CSV file with messy accounting software format.
        Supports: .xlsx, .xls, .csv, and SpreadsheetML XML format
        
        Returns:
            pd.DataFrame: Cleaned dataframe with extracted party names and phone numbers
        """
        try:
            # Handle SpreadsheetML format (.xls XML files)
            if self.file_path.endswith('.xls'):
                try:
                    raw_df = pd.read_excel(self.file_path, sheet_name=0, engine='openpyxl')
                except:
                    try:
                        raw_df = pd.read_excel(self.file_path, sheet_name=0, engine='xlrd')
                    except:
                        # Fallback to XML parsing for SpreadsheetML
                        raw_df = self._parse_spreadsheet_xml(self.file_path)
            elif self.file_path.endswith('.csv'):
                raw_df = pd.read_csv(self.file_path)
            else:
                raw_df = pd.read_excel(self.file_path, sheet_name=0)
            
            logger.info(f"Loaded file with shape: {raw_df.shape}")
            
            # Skip the first 4 rows (junk header)
            df = raw_df.iloc[4:].reset_index(drop=True)
            
            # Find the actual header row containing: DATE, BILLNO, AGENT, DAYS, NETAMT, BALAMT, HASTE, PHONE, MOBILE
            header_row_idx = self._find_header_row(df)
            
            if header_row_idx == -1:
                logger.error("Could not find header row with required columns")
                return None
            
            logger.info(f"Header row found at index: {header_row_idx}")
            
            # Set headers and remove everything above
            df = df.iloc[header_row_idx:]
            df.columns = df.iloc[0]
            df = df.iloc[1:].reset_index(drop=True)
            
            # Extract party names from "Party :" rows and forward fill
            df = self._extract_and_forward_fill_party_names(df)
            
            # Remove rows where BILLNO is NaN/empty
            df = df.dropna(subset=['BILLNO'])
            df = df[df['BILLNO'].astype(str).str.strip() != '']
            df.reset_index(drop=True, inplace=True)
            
            logger.info(f"Data after removing junk rows: {len(df)} rows")
            
            # Clean phone numbers
            df = self._clean_phone_numbers(df)
            
            # Convert DAYS and BALAMT to numeric
            df = self._ensure_numeric_columns(df)
            
            logger.info(f"Final parsed dataframe shape: {df.shape}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error parsing file: {e}", exc_info=True)
            return None
    
    def _parse_spreadsheet_xml(self, file_path):
        """
        Parse SpreadsheetML XML format (.xls files that are actually XML)
        Converts to DataFrame compatible with the rest of the parser
        """
        try:
            ET.register_namespace('s', 'urn:schemas-microsoft-com:office:spreadsheet')
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'s': 'urn:schemas-microsoft-com:office:spreadsheet'}
            rows = root.findall('.//s:Row', ns)
            
            logger.info(f"XML: Found {len(rows)} rows")
            
            data = []
            for row in rows:
                cells = row.findall('s:Cell', ns)
                row_data = []
                for cell in cells:
                    # Handle merged cells
                    merge_attr = cell.get('MergeAcross')
                    merge_count = int(merge_attr) + 1 if merge_attr else 1
                    
                    data_elem = cell.find('s:Data', ns)
                    value = data_elem.text if data_elem is not None else None
                    row_data.append(value)
                    
                    # Add empty cells for merged ones
                    for _ in range(merge_count - 1):
                        row_data.append(None)
                
                data.append(row_data)
            
            # Create DataFrame - pad rows to same length
            max_len = max(len(row) for row in data) if data else 0
            padded_data = [row + [None] * (max_len - len(row)) for row in data]
            
            df = pd.DataFrame(padded_data)
            logger.info(f"XML parsed: {df.shape} shape")
            return df
        
        except Exception as e:
            logger.error(f"Error parsing SpreadsheetML XML: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _find_header_row(self, df):
        """
        Dynamically find the row containing headers:
        DATE, BILLNO, AGENT, DAYS, NETAMT, BALAMT, HASTE, PHONE, MOBILE
        """
        required_headers = {'DATE', 'BILLNO', 'AGENT', 'DAYS', 'NETAMT', 'BALAMT', 'HASTE', 'PHONE', 'MOBILE'}
        
        for idx, row in df.iterrows():
            # Convert row to string and check if it contains required headers
            row_str = ' '.join(str(val).upper().strip() for val in row if pd.notna(val))
            
            # Check if all required headers are present
            found_headers = set()
            for header in required_headers:
                if header in row_str:
                    found_headers.add(header)
            
            if len(found_headers) >= 8:  # At least 8 out of 9 headers found
                logger.info(f"Found {len(found_headers)} headers in row {idx}")
                return idx
        
        return -1
    
    def _extract_and_forward_fill_party_names(self, df):
        """
        Extract customer names from "Party : [Name]" rows and forward fill to bill rows.
        Handles multiple formats:
        - "Party : Name. Address" -> Extracts: Name
        - "Party : Name : Address" -> Extracts: Name  
        - "Party : Name (Address)" -> Extracts: Name
        
        This function:
        1. Identifies rows starting with "Party :" in the first cell
        2. Extracts the customer name (before delimiter: dot, colon, or parenthesis)
        3. Marks these rows for removal
        4. Forward fills the Party name to subsequent bill rows
        5. Removes the "Party :" marker rows
        """
        party_column = []
        current_party = "Unknown"
        rows_to_drop = []
        
        for idx, row in df.iterrows():
            first_cell = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            
            # Check if this is a "Party :" row
            if first_cell.upper().startswith("PARTY:") or first_cell.upper().startswith("PARTY :"):
                # Extract party name - handles different delimiters
                # Pattern: "Party : Name : Address" or "Party : Name. Address" or "Party : Name (Address)"
                
                # First, try to match " : " (space-colon-space) pattern - most reliable
                match = re.search(r'Party\s*:\s*(.+?)\s+:\s+', first_cell, re.IGNORECASE)
                
                if not match:
                    # Try dot separator " . "
                    match = re.search(r'Party\s*:\s*(.+?)\s*\.\s+', first_cell, re.IGNORECASE)
                
                if not match:
                    # Try parenthesis separator  
                    match = re.search(r'Party\s*:\s*(.+?)\s*\(', first_cell, re.IGNORECASE)
                
                if match:
                    extracted = match.group(1).strip()
                    current_party = extracted.rstrip('.: ')
                    logger.info(f"Found party: {current_party}")
                else:
                    # Fallback: just remove "Party :" prefix and use everything after
                    temp = re.sub(r'Party\s*:\s*', '', first_cell, flags=re.IGNORECASE).strip()
                    current_party = temp
                    logger.info(f"Found party (fallback): {current_party}")
                
                rows_to_drop.append(idx)
            else:
                # This is a bill row, assign current party
                party_column.append(current_party)
        
        # Remove the rows_to_drop indices that are within the valid range
        valid_drop_indices = [idx for idx in rows_to_drop if idx < len(df)]
        df = df.drop(valid_drop_indices).reset_index(drop=True)
        
        # Verify party_column length matches new df length
        if len(party_column) == len(df):
            df['Party'] = party_column
        else:
            logger.warning(f"Party column length mismatch: {len(party_column)} vs {len(df)}")
            df['Party'] = "Unknown"
        
        return df
    
    def _clean_phone_numbers(self, df):
        """
        Extract and validate phone numbers from PHONE and MOBILE columns.
        Checks both columns and uses the one with valid 10-digit number.
        Priority: MOBILE > PHONE (if both have valid numbers)
        
        Creates PHONE_NUMBER column with full country code for valid 10-digit numbers.
        """
        def extract_10_digit_phone(phone_str):
            """Extract 10-digit phone number from string"""
            if pd.isna(phone_str) or phone_str == "" or str(phone_str).strip() == "None":
                return None
            
            # Remove all non-numeric characters
            phone_digits = re.sub(r'\D', '', str(phone_str).strip())
            
            # Keep only last 10 digits if more than 10
            if len(phone_digits) > 10:
                phone_digits = phone_digits[-10:]
            
            # Return if exactly 10 digits
            if len(phone_digits) == 10:
                return phone_digits
            
            return None
        
        def get_combined_phone(row):
            """
            Extract phone from MOBILE or PHONE column (whichever has valid 10-digit number)
            Priority: Try MOBILE first, then PHONE
            """
            phone_num = None
            
            # Try MOBILE column first
            if 'MOBILE' in row.index and pd.notna(row.get('MOBILE')):
                phone_num = extract_10_digit_phone(row['MOBILE'])
            
            # If no valid number from MOBILE, try PHONE
            if not phone_num and 'PHONE' in row.index and pd.notna(row.get('PHONE')):
                phone_num = extract_10_digit_phone(row['PHONE'])
            
            # Return with country code if valid
            if phone_num:
                return f"{self.country_code}{phone_num}"
            
            return None
        
        # Add combined PHONE_NUMBER column
        df['PHONE_NUMBER'] = df.apply(get_combined_phone, axis=1)
        
        logger.info(f"Phone numbers extracted: {df['PHONE_NUMBER'].notna().sum()} rows with valid 10-digit numbers")
        
        return df
    
    def _ensure_numeric_columns(self, df):
        """Convert DAYS and BALAMT to numeric types"""
        
        # Convert DAYS to int
        if 'DAYS' in df.columns:
            df['DAYS'] = pd.to_numeric(df['DAYS'], errors='coerce').fillna(0).astype(int)
        
        # Convert BALAMT to float
        if 'BALAMT' in df.columns:
            df['BALAMT'] = pd.to_numeric(df['BALAMT'], errors='coerce').fillna(0.0)
        
        # Also convert NETAMT if present
        if 'NETAMT' in df.columns:
            df['NETAMT'] = pd.to_numeric(df['NETAMT'], errors='coerce').fillna(0.0)
        
        return df
    
    def filter_by_days(self, df, min_days):
        """
        Filter dataframe to keep only rows where DAYS >= min_days and has valid cleaned phone.
        Also identify accounts without phone numbers.
        
        Args:
            df (pd.DataFrame): Input dataframe
            min_days (int): Minimum days threshold
        
        Returns:
            tuple: (filtered_df, accounts_without_phone)
        """
        if 'DAYS' not in df.columns:
            logger.error("DAYS column not found in dataframe")
            return df, []
        
        if 'PHONE_NUMBER' not in df.columns:
            logger.error("PHONE_NUMBER column not found in dataframe")
            return df.iloc[0:0], pd.DataFrame(columns=['Party', 'BILLNO', 'DAYS', 'BALAMT'])
        
        # First filter by days
        filtered = df[df['DAYS'] >= min_days].copy()
        
        # Identify accounts without phone numbers
        accounts_without_phone = filtered[
            (filtered['PHONE_NUMBER'].isna()) |
            (filtered['PHONE_NUMBER'].astype(str).str.strip() == "") |
            (filtered['PHONE_NUMBER'].astype(str).str.strip() == "None")
        ].groupby('Party')[['BILLNO', 'DAYS', 'BALAMT']].agg({
            'BILLNO': lambda x: ', '.join(x.astype(str)),
            'DAYS': lambda x: f"{int(x.max())} days",
            'BALAMT': 'sum'
        }).reset_index()
        
        # Remove accounts without phone from filtered list
        filtered = filtered[
            (filtered['PHONE_NUMBER'].notna()) &
            (filtered['PHONE_NUMBER'].astype(str).str.strip() != "") &
            (filtered['PHONE_NUMBER'].astype(str).str.strip() != "None")
        ].copy()
        
        logger.info(f"Filtered from {len(df)} to {len(filtered)} rows (min_days={min_days})")
        if not accounts_without_phone.empty:
            logger.info(f"Found {len(accounts_without_phone)} accounts without phone numbers")
        
        return filtered, accounts_without_phone
    
    def validate_dataframe(self, df):
        """Validate that required columns exist"""
        required_cols = {'Party', 'BILLNO', 'BALAMT', 'DAYS'}
        phone_cols = {'MOBILE', 'PHONE'}
        
        missing_required = required_cols - set(df.columns)
        missing_phone = phone_cols & set(df.columns)
        
        if missing_required:
            logger.error(f"Missing required columns: {missing_required}")
            return False
        
        if not missing_phone:
            logger.error("Neither MOBILE nor PHONE column found")
            return False
        
        return True

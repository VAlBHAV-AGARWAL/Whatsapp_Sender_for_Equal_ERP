import xml.etree.ElementTree as ET

# Register namespace to avoid ns issue
ET.register_namespace('s', 'urn:schemas-microsoft-com:office:spreadsheet')
ET.register_namespace('x', 'urn:schemas-microsoft-com:office:excel')
ET.register_namespace('o', 'urn:schemas-microsoft-com:office:office')

tree = ET.parse('12345.xls')
root = tree.getroot()

# Define namespaces
ns = {'s': 'urn:schemas-microsoft-com:office:spreadsheet'}

# Find all rows directly
rows = root.findall('.//s:Row', ns)
print(f"Found {len(rows)} rows\n")

# Extract data
data = []
for idx, row in enumerate(rows[:30]):  # First 30 rows
    cells = row.findall('s:Cell', ns)
    row_data = []
    col_count = 0
    for cell in cells:
        # Check for colspan
        merge_attr = cell.get('MergeAcross')
        merge_count = int(merge_attr) + 1 if merge_attr else 1
        
        data_elem = cell.find('s:Data', ns)
        value = data_elem.text if data_elem is not None else None
        row_data.append(value)
        
        # Add empty cells for merged ones
        for _ in range(merge_count - 1):
            row_data.append(None)
        col_count += merge_count
    
    data.append(row_data)
    print(f"Row {idx} ({col_count} cols): {row_data[:10]}")  # Show first 10 columns

print(f"\n\nTotal rows analyzed: {len(data)}")

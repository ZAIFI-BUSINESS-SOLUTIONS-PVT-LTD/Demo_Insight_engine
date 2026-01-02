import pandas as pd
import os

file_path = "reference_inputs/online_sample.xlsx"
try:
    xls = pd.ExcelFile(file_path)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"--- Sheet: {sheet} ---")
        print("Columns head:", list(df.columns)[:10])
        first_row = df.iloc[0]
        print("Row 0:", first_row.tolist()[:10])
        # Find row with data
        print("Head 5:")
        print(df.head(5))
except Exception as e:
    print(e)

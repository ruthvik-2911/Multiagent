import pandas as pd

file_path = r"data\Analytics\sales.xlsx"

df = pd.read_excel(file_path)

print("=" * 50)
print("EXCEL CONTENT")
print("=" * 50)

print(df)

print("\n")

print("Total Rows:", len(df))
print("Total Columns:", len(df.columns))

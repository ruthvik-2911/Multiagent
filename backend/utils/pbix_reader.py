import os
import pandas as pd
from pbixray import PBIXRay

def read_pbix_and_extract_csv(path: str) -> str:
    """
    Extracts tabular data from a Power BI (.pbix) file using pbixray,
    saves the tables as CSVs in an uploads/extracted_pbix/ directory,
    and returns a summary text of the schema for the LLM to index.
    """
    model = PBIXRay(path)
    
    file_name = os.path.basename(path)
    base_name = os.path.splitext(file_name)[0]
    
    # Create extraction directory
    extract_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(path))), "uploads", "extracted_pbix", base_name)
    os.makedirs(extract_dir, exist_ok=True)
    
    summary_parts = [
        f"POWER BI DASHBOARD DATA: {file_name}",
        "The following tables were extracted from this Power BI file:"
    ]
    
    try:
        tables = model.tables
    except Exception as e:
        return f"Power BI Dashboard: {file_name}. Could not extract tables due to unsupported compression or error: {str(e)}"
        
    for table_name in tables:
        # PBIXRay handles tabular data directly
        try:
            df = model.get_table(table_name)
            if df is not None and not df.empty:
                csv_path = os.path.join(extract_dir, f"{table_name}.csv")
                df.to_csv(csv_path, index=False)
                
                # Append schema to summary so LLM knows what columns exist
                columns = ", ".join(df.columns.tolist())
                summary_parts.append(f"\nTable: {table_name}")
                summary_parts.append(f"Columns: {columns}")
                summary_parts.append(f"Row Count: {len(df)}")
                summary_parts.append(f"File Path: {csv_path}")
        except Exception as e:
            summary_parts.append(f"\nTable: {table_name} (Failed to extract: {str(e)})")
            
    return "\n".join(summary_parts)

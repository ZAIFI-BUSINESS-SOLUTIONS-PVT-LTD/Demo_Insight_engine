import pandas as pd
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SheetExtractor:
    """
    Helper to extract a specific sheet from a multi-sheet Excel workbook 
    and save it as a standalone Excel file.
    """
    
    @staticmethod
    def extract(source_path: str, sheet_name: str, output_path: str) -> bool:
        """
        Extracts `sheet_name` from `source_path` to `output_path`.
        Returns True if successful, False if sheet not found.
        """
        if not os.path.exists(source_path):
             logger.warning(f"Source file not found: {source_path}")
             return False
             
        try:
            # Inspection first to avoid full load if possible? 
            # Pandas read_excel with sheet_name loads just that sheet usually.
            # However, we need to check if sheet exists first.
            xls = pd.ExcelFile(source_path)
            
            # Case sensitive match required by constraints
            if sheet_name not in xls.sheet_names:
                logger.warning(f"Sheet '{sheet_name}' not found in {source_path}. Available: {xls.sheet_names}")
                return False
                
            logger.info(f"Extracting sheet '{sheet_name}' from {source_path}...")
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None) # Read raw, no header inference here
            
            # Save to new Excel with specific sheet name to allow Transformer to match it
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                
            logger.info(f"Saved extracted sheet '{sheet_name}' to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract sheet {sheet_name}: {e}")
            raise e

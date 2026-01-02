import pandas as pd
import logging
import re
from typing import Tuple, Dict
from src.phase0.interface import ResponseTransformer

logger = logging.getLogger(__name__)

class OfflineResponseTransformer(ResponseTransformer):
    def transform(self, input_path: str, target_class: str) -> Tuple[pd.DataFrame, Dict[int, str]]:
        logger.info(f"Processing Offline Format: {input_path} for class {target_class}")
        
        try:
            xls = pd.ExcelFile(input_path)
            extracted_key = {}
            # Structure: {student_id: {question_id: selected_option}}
            students_dict = {}
            
            normalized_target = target_class.lower().replace("class_", "").replace("_", "").replace(" ", "")
            processed_sheets = 0
            
            # Track max Q for matrix dim
            max_q_id_found = 0
            
            for sheet_name in xls.sheet_names:
                # Filter Sheet
                s_name_clean = sheet_name.lower().replace(" ", "").replace("_", "")
                
                # Check match
                # offline_sample had keys like "9FB", "MEDICAL". "Medical" might be the class?
                # If target is "class_10", and sheet is "10FB", match.
                
                if normalized_target not in s_name_clean:
                    if "class" in normalized_target:
                         t_num = normalized_target.replace("class", "")
                         if t_num not in s_name_clean:
                              continue
                    else: 
                         # If target is generic, maybe proceed? But usually explicit.
                         # If sheet name is wildly different (e.g. "Instructions"), skip.
                         # We'll stick to containment.
                         continue
                
                logger.info(f"Processing Sheet: {sheet_name}")
                processed_sheets += 1
                
                # Read header=None
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                
                # Find Header Row (Q1, Q2...)
                header_row_idx = -1
                
                for idx, row in df.iterrows():
                    row_values = [str(v).strip().upper() for v in row.values if pd.notna(v)]
                    if "Q1" in row_values and "Q2" in row_values:
                        header_row_idx = idx
                        break
                
                if header_row_idx == -1:
                    logger.warning(f"No Q1... header found in {sheet_name}. Skipping.")
                    continue
                    
                # Parse Header
                header_row = df.iloc[header_row_idx]
                q_col_map = {}
                student_id_col_idx = 0
                
                # Find ID col
                # Usually Col 0 or labeled.
                # In sample: Col 0 is "CANDIDATE ID"
                
                for col_idx, cell_val in enumerate(header_row):
                    val_str = str(cell_val).strip().upper() if pd.notna(cell_val) else ""
                    
                    if val_str in ["CANDIDATE ID", "ROLL NO", "ID", "STUDENT ID"]:
                        student_id_col_idx = col_idx
                    
                    m = re.match(r"^Q\s*(\d+)$", val_str)
                    if m:
                        q_num = int(m.group(1))
                        q_col_map[col_idx] = q_num
                        if q_num > max_q_id_found: max_q_id_found = q_num
                
                if not q_col_map:
                    logger.warning("No Question Columns found.")
                    continue
                    
                # Process Data Rows
                # Look for ANSWER KEY row
                # In sample, row after header has "0" ID and "ANSWER KEY" Name.
                # Let's iterate all rows.
                
                data_rows = df.iloc[header_row_idx + 1:]
                
                for _, row in data_rows.iterrows():
                    # Check ID col
                    raw_id = row.iloc[student_id_col_idx]
                    id_str = str(raw_id).strip().upper() if pd.notna(raw_id) else ""
                    
                    # Check Name col? Usually Col 1 is Name.
                    # Sample: Col 1 is "CANDIDATE NAME" -> Value "ANSWER KEY"
                    # But we don't rely on Col 1 index.
                    # Scan for "ANSWER KEY" in the whole row?
                    
                    # Detect Answer Key Row
                    row_values_str = [str(v).strip().upper() for v in row.values if pd.notna(v)]
                    is_key_row = "ANSWER KEY" in row_values_str
                    
                    if is_key_row:
                        # Extract Key
                        for col_idx, q_num in q_col_map.items():
                            val = row.iloc[col_idx]
                            k_char = str(val).strip().upper() if pd.notna(val) else ""
                            if k_char in ['A', 'B', 'C', 'D']:
                                extracted_key[q_num] = k_char
                        continue
                    
                    # Normal Student Row
                    # Skip junk
                    if id_str in ["", "0", "MAX MARKS", "AVERAGE", "CORRECT", "WRONG", "TOTR"]:
                        continue
                    
                    # Must be numeric-ish ID?
                    # "274600"
                    
                    # Init student
                    if id_str not in students_dict:
                        students_dict[id_str] = {}
                    
                    for col_idx, q_num in q_col_map.items():
                         val = row.iloc[col_idx]
                         sel_char = str(val).strip().upper() if pd.notna(val) else ""
                         if sel_char not in ['A', 'B', 'C', 'D']:
                             sel_char = ""
                         
                         # Populate Matrix
                         # Store if present? Or store empty string?
                         # Storing all ensures structure, but dict overhead. 
                         # We'll rely on DataFrame(dict) to handle missing keys as NaN.
                         # But let's be explicit with EMPTY values for known Questions if we want 'unattempted' to be empty string now?
                         # The requirement is "If unattempted: Leave cell EMPTY".
                         # If we don't put it in dict, and other questions are there, it's NaN.
                         # We'll fillna("") at end.
                         if sel_char:
                             students_dict[id_str][q_num] = sel_char
            
            if processed_sheets == 0:
                 logger.error(f"No sheets matched {target_class}")
                 # raise ValueError? Or Just return empty?
                 # If we are required to produce output, raise.
                 raise ValueError("No matching sheets found for class.")

            if not students_dict:
                raise ValueError("No student data found.")
            
            # Construct Matrix
            df_matrix = pd.DataFrame(students_dict)
            
            # Reindex Qs
            df_matrix = df_matrix.reindex(range(1, max_q_id_found + 1))
            df_matrix = df_matrix.fillna("")
            df_matrix.index.name = "question_id"
            
            return df_matrix, extracted_key

        except Exception as e:
            logger.error(f"Error transforming Offline format: {e}")
            raise e

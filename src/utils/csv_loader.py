import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def load_student_responses(file_path: str) -> pd.DataFrame:
    """
    Loads response sheet. Handles .xlsx or .csv.
    Standardizes format:
    - Index: Student ID
    - Columns: Question IDs (e.g., "Q1", "Q2")
    - Values: Selected Option (A, B, C, D)
    """
    if not os.path.exists(file_path):
        # Fallback for xlsx if csv requested but missing
        base, ext = os.path.splitext(file_path)
        if ext == '.csv' and os.path.exists(base + '.xlsx'):
            file_path = base + '.xlsx'
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Loading responses from {file_path}")
    
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    # Detect if transposed (Questions as rows)
    # Heuristic: verify if 'QuestionID' or 'question_id' is a column
    if 'QuestionID' in df.columns or 'question_id' in df.columns:
        logger.info("Detected transposed format (Questions as rows). Pivoting...")
        # Make QuestionID the index
        col_name = 'QuestionID' if 'QuestionID' in df.columns else 'question_id'
        df.set_index(col_name, inplace=True)
        # Transpose: Now Rows=Students, Cols=Questions
        df = df.T
    
    # Standardize Column Names (Questions)
    # Expected: 1, 2, 3... -> Q1, Q2, Q3...
    new_cols = {}
    for col in df.columns:
        try:
            # Check if column is integer-like
            q_num = int(col)
            new_cols[col] = f"Q{q_num}"
        except:
            # Keep as is if not a number
            pass
    
    df.rename(columns=new_cols, inplace=True)
    df.index.name = "student_id"
    
    logger.info(f"Loaded {len(df)} students and {len(df.columns)} questions.")
    return df

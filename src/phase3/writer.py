import os
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OUTPUT_FILE = "class_level_focus_and_action.csv"
COLUMNS = [
    "class_id",
    "focus_zone_1", "focus_zone_2", "focus_zone_3",
    "action_plan_1", "action_plan_2", "action_plan_3"
]

def save_manifest(results: list[dict]):
    """
    Saves the list of class insights to a CSV file.
    Enforces strict schema compliance.
    """
    output_dir = Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, OUTPUT_FILE)
    
    df = pd.DataFrame(results)
    
    # Enforce Schema
    current_cols = list(df.columns)
    
    # 1. Check for missing columns
    missing = [c for c in COLUMNS if c not in current_cols]
    if missing:
        logger.error(f"Schema Violation: Missing columns {missing}")
        raise ValueError(f"Schema Violation: Missing columns {missing}")
        
    # 2. Check for extra columns
    extra = [c for c in current_cols if c not in COLUMNS]
    if extra:
        logger.error(f"Schema Violation: Extra columns found {extra}")
        # Strict mode: Abort. Or drop them? 
        # Prompt says "No extra columns... If schema mismatch occurs: Log ERROR... Abort".
        raise ValueError(f"Schema Violation: Extra columns {extra}")
        
    # Reorder strictly
    df = df[COLUMNS]
    
    # Cardinality check: "Exactly one row per class"
    # The 'results' list contains one dict per processed class. 
    # If duplicates exists, it's a logic error upstream.
    if len(df["class_id"].unique()) != len(df):
        logger.error("Cardinality Violation: Duplicate rows for same class_id found.")
        raise ValueError("Cardinality Violation: Duplicate class_id")
        
    try:
        # Header must always be written (default is True)
        df.to_csv(file_path, index=False)
        logger.info(f"Successfully wrote Phase 3 manifest to {file_path}")
    except Exception as e:
        logger.error(f"Failed to write output CSV: {e}")
        raise

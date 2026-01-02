import os
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

REQUIRED_COLUMNS = [
    "student_id",
    "strongest_concepts",
    "weakest_concepts",
    "dominant_mistake_pattern",
    "llm_summary"
]

def load_class_data(class_id: str) -> str:
    """
    Reads the Phase 2 summary CSV for the given class.
    Returns the CSV content as a string for the LLM.
    Raises FileNotFoundError or ValueError if validation fails.
    """
    file_path = os.path.join(Config.OUTPUT_DIR, class_id, "phase2", "student_insight_summary.csv")
    
    if not os.path.exists(file_path):
        logger.error(f"Missing Phase 2 output for {class_id}: {file_path}")
        raise FileNotFoundError(f"Missing Phase 2 output: {file_path}")
        
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV for {class_id}: {e}")
        raise ValueError(f"Corrupt CSV file: {file_path}")
        
    # Validation
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing columns in {file_path}: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    # Return as string (CSV format)
    # We only need the required columns to save token space if there are extra columns (though per spec there shouldn't be)
    return df[REQUIRED_COLUMNS].to_csv(index=False)


# Guardrail to prevent Phase 1 execution if input directory contains restricted files
import os
from src.config import Config

def check_input_purity(class_id: str = None):
    target = class_id or Config.DEFAULT_CLASS
    input_dir = os.path.join(Config.INPUT_DIR, target)
    if not os.path.exists(input_dir):
        return
        
    for f in os.listdir(input_dir):
        if f.lower().endswith(".xlsx") or f.lower().endswith(".xls"):
            raise ValueError(f"CRITICAL: Phase 1 Guardrail Failed. Restricted file found in input: {f}. Phase 1 must not see Excel files.")

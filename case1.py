import sys
import os
import json
import logging
import traceback

# Ensure we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase1 import extract_questionpaper
from src.phase1 import add_subjects
from src.phase1 import add_chapters_topics
from src.phase1 import merge_data
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case1Runner")

def verify_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Verification Failed: File not found - {path}")
    if os.path.getsize(path) == 0:
        raise ValueError(f"Verification Failed: File is empty - {path}")
    logger.info(f"Verified exists: {path}")

def verify_json_schema(path, required_keys, root_list_key=None):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if root_list_key:
        if not isinstance(data, dict) or root_list_key not in data:
            raise ValueError(f"Verification Failed: Root object with key '{root_list_key}' required in {path}")
        data = data[root_list_key]

    if not isinstance(data, list):
        raise ValueError(f"Verification Failed: Data must be a list in {path}")
        
    if not data:
        logger.warning(f"Warning: JSON is empty list in {path}")
        return

    first_item = data[0]
    missing = [k for k in required_keys if k not in first_item]
    if missing:
        raise ValueError(f"Verification Failed: Missing keys {missing} in {path}")
    
    logger.info(f"Verified schema for {path}")

def verify_input_files(current_class):
    """Verify required input files exist for a class"""
    input_dir = os.path.join(Config.INPUT_DIR, current_class)
    
    # Check for PDF (flexible naming)
    pdf_candidates = ["QuestionPaper.pdf", "question_paper.pdf", "questionpaper.pdf"]
    pdf_found = False
    for pdf_name in pdf_candidates:
        if os.path.exists(os.path.join(input_dir, pdf_name)):
            pdf_found = True
            logger.info(f"Verified input file: {pdf_name}")
            break
    
    if not pdf_found:
        # Try to find any PDF
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            raise FileNotFoundError(f"No question paper PDF found in {input_dir}")
        logger.info(f"Verified input file: {pdf_files[0]}")
    
    # Check for required CSV files
    required_csvs = ["answer_key.csv", "response_sheet.csv"]
    for filename in required_csvs:
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Required input file missing: {filepath}")
        logger.info(f"Verified input file: {filename}")
    
    return True

def main():
    try:
        target_class = os.getenv("TARGET_CLASS")
        classes_to_process = []

        if not target_class or target_class.strip().lower() == "none":
            # Detect all classes in input directory
            if os.path.exists(Config.INPUT_DIR):
                classes_to_process = [d for d in os.listdir(Config.INPUT_DIR) 
                                      if os.path.isdir(os.path.join(Config.INPUT_DIR, d))]
        else:
            classes_to_process = [target_class]

        if not classes_to_process:
            logger.error("No classes found to process.")
            sys.exit(1)

        logger.info(f"Classes to process: {classes_to_process}")

        for current_class in classes_to_process:
            # Patch Config.DEFAULT_CLASS for this iteration
            Config.DEFAULT_CLASS = current_class
            
            logger.info(f"=== Starting Phase 1 Execution for {current_class} ===")
            
            # Verify input files
            try:
                verify_input_files(current_class)
            except FileNotFoundError as e:
                logger.error(f"Input validation failed for {current_class}: {e}")
                continue
            
            # 1. Extract Question Paper
            logger.info(f"--- Step 1: Extract Question Paper ({current_class}) ---")
            extract_questionpaper.process()
            
            # 2. Add Subject Assignments (Interactive)
            logger.info(f"--- Step 2: Assign Subjects to Questions ({current_class}) ---")
            add_subjects.process()
            
            # 3. Add Chapter and Topic Assignments (LLM-based)
            logger.info(f"--- Step 3: Assign Chapters and Topics to Questions ({current_class}) ---")
            add_chapters_topics.process()
            
            # 4. Merge Data (reads answer_key.csv and response_sheet.csv)
            logger.info(f"--- Step 4: Merge Data ({current_class}) ---")
            merge_data.process()
            
            # 3. Verification
            logger.info(f"=== Verifying Outputs for {current_class} ===")
            
            qp_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase1", "questionpaper.json")
            merged_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase1", "merged.json")

            try:
                verify_file(qp_path)
                verify_file(merged_path)
                
                verify_json_schema(qp_path, ["question_number", "question_text", "options"], root_list_key="questions")
                verify_json_schema(merged_path, ["student_id", "question_id", "question_text", "options", "correct_option", "student_selected_option"])
                
                logger.info(f"=== SUCCESS: {current_class} Completed and Verified ===")
            except Exception as e:
                logger.error(f"Verification Failed for {current_class}: {e}")
    except Exception:
        logger.error("Execution FAILED")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

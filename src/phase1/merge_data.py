import os
import json
import logging
import re
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def process():
    logger.info("Starting Phase 1: Merge Data")
    
    # Paths
    qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")
    answer_key_path = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS, "answer_key.csv")
    response_sheet_path = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS, "response_sheet.csv")
    output_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "merged.json")
    
    # Validate input files exist
    if not os.path.exists(qp_path):
        # Fallback: search for any class folder that contains phase1/questionpaper.json
        import glob
        pattern = os.path.join(Config.OUTPUT_DIR, "*", "phase1", "questionpaper.json")
        matches = glob.glob(pattern)
        if matches:
            qp_path = matches[0]
            logger.info(f"Using found question paper JSON at: {qp_path}")
            print(f"Found questionpaper.json at: {qp_path}")
        else:
            raise FileNotFoundError(f"Question Paper JSON not found: {qp_path}")
    if not os.path.exists(answer_key_path):
        raise FileNotFoundError(f"Answer Key CSV not found: {answer_key_path}")
    if not os.path.exists(response_sheet_path):
        raise FileNotFoundError(f"Response Sheet CSV not found: {response_sheet_path}")
        
    # Read Question Paper JSON
    logger.info(f"Reading question paper from: {qp_path}")
    with open(qp_path, 'r', encoding='utf-8') as f:
        qp_data = json.load(f)
        questions = qp_data.get("questions") if isinstance(qp_data, dict) else qp_data
    
    # Build question map: question_number -> question details
    question_map = {}
    for q in questions:
        q_num = q.get("question_number")
        if q_num:
            # Normalize options: keep list and also provide labeled map A-D
            opts = q.get("options", []) or []
            # Ensure options is a list of strings
            if not isinstance(opts, list):
                try:
                    opts = list(opts)
                except Exception:
                    opts = []

            options_map = {}
            labels = ["A", "B", "C", "D"]

            def _clean_option(text: str) -> str:
                if not isinstance(text, str):
                    return text
                # Remove leading numeric labels like '(1) ', '1) ', '1. ' etc.
                cleaned = re.sub(r'^\s*\(?\s*\d+\s*\)?[\.)\-]*\s*', '', text)
                return cleaned.strip()

            for i, label in enumerate(labels):
                raw = opts[i] if i < len(opts) else ""
                options_map[label] = _clean_option(raw)

            question_map[int(q_num)] = {
                "question_text": q.get("question_text", ""),
                "options": opts,
                "options_map": options_map,
                "subject": q.get("subject", "Unknown"),
                "chapter": q.get("chapter", "Unknown"),
                "topic": q.get("topic", "Unknown")
            }
    
    logger.info(f"Loaded {len(question_map)} questions from questionpaper.json")
    
    # Read Answer Key CSV (format: question_id,Answer)
    logger.info(f"Reading answer key from: {answer_key_path}")
    df_answer = pd.read_csv(answer_key_path)
    # Normalize column names (trim spaces)
    df_answer.columns = df_answer.columns.str.strip()
    
    # Build answer map: question_number -> correct_option
    answer_map = {}
    for _, row in df_answer.iterrows():
        q_id = int(row.iloc[0])  # First column is question_id
        correct_ans = str(row.iloc[1]).strip().upper()  # Second column is Answer
        answer_map[q_id] = correct_ans
    
    logger.info(f"Loaded {len(answer_map)} answers from answer_key.csv")
    
    # Read Response Sheet CSV (format: question_id as first col, students as remaining cols)
    logger.info(f"Reading response sheet from: {response_sheet_path}")
    df_response = pd.read_csv(response_sheet_path)
    
    # First column is question_id, rest are student IDs
    question_col = df_response.columns[0]
    student_cols = df_response.columns[1:]
    
    logger.info(f"Found {len(student_cols)} students in response sheet")
    
    # Build merged data: list of student-question records
    merged_data = []
    
    for _, row in df_response.iterrows():
        q_num = int(row[question_col])
        
        # Get question details
        q_details = question_map.get(q_num)
        if not q_details:
            logger.warning(f"Question {q_num} not found in questionpaper.json, skipping")
            continue
            
        # Get correct answer
        correct_option = answer_map.get(q_num)
        if not correct_option:
            logger.error(f"CRITICAL: No correct answer for question {q_num} in answer_key.csv")
            raise ValueError(f"Missing correct answer for question {q_num}")
        
        # For each student, create a record
        for student_id in student_cols:
            selected_option = str(row[student_id]).strip().upper() if pd.notna(row[student_id]) else ""
            
            # Handle empty or invalid responses
            if selected_option not in ['A', 'B', 'C', 'D']:
                selected_option = ""
            
            merged_data.append({
                "student_id": str(student_id),
                "question_id": q_num,
                "question_text": q_details["question_text"],
                "options_map": q_details.get("options_map", {}),
                "subject": q_details.get("subject", "Unknown"),
                "chapter": q_details.get("chapter", "Unknown"),
                "topic": q_details.get("topic", "Unknown"),
                "correct_option": correct_option,
                "student_selected_option": selected_option
            })
    
    logger.info(f"Created {len(merged_data)} student-question records")
    
    # Save merged.json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4)
        
    logger.info(f"Saved merged data to {output_path}")

if __name__ == "__main__":
    process()

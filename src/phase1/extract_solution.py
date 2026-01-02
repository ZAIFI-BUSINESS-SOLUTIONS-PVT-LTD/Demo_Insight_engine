import os
import json
import logging
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.pdf_loader import load_pdf_pages
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.prompts import PHASE_1_EXTRACT_SOLUTION_PROMPT

logger = setup_logger(__name__)

def load_answer_key_csv(csv_path):
    logger.info(f"Loading Answer Key from CSV: {csv_path}")
    try:
        # Rules: Ignore Row 1 (header). Col A=QNum, Col B=Option.
        # header=0 means first row is header. We can skip it or just read it.
        # "Ignore the first row completely" -> skip_match logic? 
        # Usually pd.read_csv(header=0) treats row 1 as header. 
        # If user says ignor row 1, maybe they mean it has junk?
        # "Row 1 is a header row ... Ignore the first row completely"
        # Means Row 2 is data.
        
        df = pd.read_csv(csv_path) 
        # Pandas reads header by default. So checking columns might be safer.
        # But instructions say "Map Column A... Column B".
        # We'll use iloc.
        
        solutions = []
        for index, row in df.iterrows():
            try:
                # Column A is index 0, Column B is index 1
                q_num_raw = row.iloc[0]
                opt_raw = row.iloc[1]
                
                # Check for nan
                if pd.isna(q_num_raw) or pd.isna(opt_raw):
                    continue
                    
                # Clean
                q_num = int(q_num_raw)
                correct_opt = str(opt_raw).strip().upper()
                
                item = {
                    "question_number": q_num,
                    "correct_option": correct_opt,
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                }
                solutions.append(item)
            except Exception as e:
                logger.warning(f"Skipping CSV row {index}: {e}")
                
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key CSV: {e}")
        raise

def load_answer_key_excel(file_path):
    logger.info(f"Loading Answer Key from Excel: {file_path}")
    try:
        df = pd.read_excel(file_path)
        solutions = []
        # We assume Col 0 = Q Num, Col 1 = Answer, similar to CSV rule
        # Or look for specific headers if possible. Inspection showed QuestionID, CorrectAnswer.
        # Let's try to detect columns or fall back to iloc.
        
        q_col = df.columns[0]
        a_col = df.columns[1]
        
        for index, row in df.iterrows():
            try:
                q_num_raw = row.iloc[0]
                opt_raw = row.iloc[1]
                
                if pd.isna(q_num_raw) or pd.isna(opt_raw):
                    continue
                    
                q_num = int(q_num_raw)
                correct_opt = str(opt_raw).strip().upper()
                
                item = {
                    "question_number": q_num,
                    "correct_option": correct_opt,
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                }
                solutions.append(item)
            except Exception as e:
                logger.warning(f"Skipping Excel row {index}: {e}")
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key Excel: {e}")
        raise

def load_answer_key_json(json_path):
    logger.info(f"Loading Answer Key from JSON: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        solutions = []
        for item in data:
            # Phase 0 JSON: {"question_id": "Q1", "correct_option": "A"} or {"question_id": 1 ...}
            # We need question_number as int
            q_id = item.get("question_id")
            opt = item.get("correct_option")
            
            if q_id is None or opt is None:
                continue
                
            # Parse number from "Q1" or 1
            q_num = None
            if isinstance(q_id, int):
                q_num = q_id
            else:
                q_id_str = str(q_id).upper()
                if q_id_str.startswith("Q"):
                    try:
                        q_num = int(q_id_str[1:])
                    except:
                        pass
                else:
                    try:
                        q_num = int(q_id_str)
                    except:
                        pass
            
            if q_num is not None:
                solutions.append({
                    "question_number": q_num,
                    "correct_option": str(opt).strip().upper(),
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                })
        
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key JSON: {e}")
        raise

def process():
    setup_gemini()
    
    class_dir = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS)
    output_dir = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "solution.json")
    
    # STRICT RULE: correctness comes ONLY from answer_key.json
    answer_key_path = os.path.join(class_dir, "answer_key.json")
    
    if not os.path.exists(answer_key_path):
        logger.error(f"CRITICAL: answer_key.json missing in {class_dir}. This is required for correctness.")
        # We must fail fast per Step 5
        raise FileNotFoundError(f"answer_key.json missing in {class_dir}")
        
    # Load Basic Solutions (Correct Options)
    base_solutions = load_answer_key_json(answer_key_path)
    if not base_solutions:
        raise ValueError(f"answer_key.json in {class_dir} yielded no data or was empty.")

    # Create a map for enrichment
    # Key: question_number (int) -> item dict
    sol_map = {item["question_number"]: item for item in base_solutions}

    # Conditional PDF Handling (Step 2)
    pdf_path = os.path.join(class_dir, "Solutions.pdf")
    if os.path.exists(pdf_path):
        logger.info(f"Solutions.pdf found. Parsing for explanations...")
        
        pdf_explanations = []
        for page_num, text in load_pdf_pages(pdf_path):
            logger.info(f"Processing Solutions PDF Page {page_num}...")
            try:
                data = call_gemini_json(PHASE_1_EXTRACT_SOLUTION_PROMPT, text)
                batch = []
                if isinstance(data, list):
                    batch = data
                elif isinstance(data, dict):
                     batch = data.get("solutions", [data]) if "solutions" in data else [data]
                
                pdf_explanations.extend(batch)
            except Exception as e:
                logger.error(f"Failed to extract from PDF page {page_num}: {e}")
                continue # specific to PDF parsing, we continue
        
        # Merge explanations into base_solutions
        # We match by question_number (or question_id if parsed)
        for exp in pdf_explanations:
            # Try to get number
            q_num = exp.get("question_number")
            # If prompt returns question_id string, parse it
            if not q_num and exp.get("question_id"):
                 # Parse "Q1" -> 1
                 try:
                     q_num = int(str(exp.get("question_id")).upper().replace("Q", ""))
                 except: 
                     pass
            
            if q_num and q_num in sol_map:
                # Update ONLY explanation fields
                current = sol_map[q_num]
                # Only update if we have meaningful text
                new_sol = exp.get("solution_text")
                new_key = exp.get("key_concept")
                
                if new_sol and "Answer key provided" not in new_sol:
                    current["solution_text"] = new_sol
                if new_key and new_key != "UNKNOWN":
                    current["key_concept"] = new_key
    else:
        logger.info("Solutions.pdf not found. Skipping explanation enrichment.")
        # Fields are already set to default/empty in load_answer_key_json or we ensure they are empty here
        # load_answer_key_json sets: solution_text="Answer key provided...", key_concept="UNKNOWN"
        # Requirement says: "Leave explanation fields as null or empty"
        # Let's clean them up if they are the placeholder
        for item in base_solutions:
            item["solution_text"] = "" 
            item["key_concept"] = ""

    # Final List Preparation
    final_solutions = list(sol_map.values())
    
    # Post-process to add question_id and Validate
    processed_final = []
    seen_ids = set()
    
    for s in final_solutions:
        try:
            q_num = s.get("question_number")
            if not q_num:
                logger.warning(f"Skipping solution without number: {s}")
                continue
                
            q_id = f"Q{q_num}"
            
            # Step 5: Duplicate check
            if q_id in seen_ids:
                logger.error(f"CRITICAL: Duplicate question_id detected: {q_id}")
                raise ValueError(f"Duplicate question_id {q_id} in solutions")
            seen_ids.add(q_id)
            
            s["question_id"] = q_id
            
            # Step 5: check correct_option
            if not s.get("correct_option"):
                logger.error(f"CRITICAL: Missing correct_option for {q_id}")
                raise ValueError(f"Missing correct_option for {q_id}")
                
            processed_final.append(s)

        except Exception as e:
            logger.error(f"Error processing item: {s} - {e}")
            raise

    logger.info(f"Extracted {len(processed_final)} solutions.")
    
    # Step 3: Wrap in root object
    output_data = {"solutions": processed_final}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    process()

import os
import json
import logging
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.pdf_loader import load_pdf_pages
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.prompts import PHASE_1_EXTRACT_QUESTION_PROMPT

logger = setup_logger(__name__)

def process():
    setup_gemini()
    
    class_input_dir = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS)
    
    # Try multiple PDF filename variations
    pdf_candidates = ["QuestionPaper.pdf", "question_paper.pdf", "questionpaper.pdf"]
    input_path = None
    
    for candidate in pdf_candidates:
        path = os.path.join(class_input_dir, candidate)
        if os.path.exists(path):
            input_path = path
            break
    
    if not input_path:
        # Fallback: find any PDF file in the directory
        if os.path.exists(class_input_dir):
            pdf_files = [f for f in os.listdir(class_input_dir) if f.lower().endswith('.pdf')]
            if pdf_files:
                input_path = os.path.join(class_input_dir, pdf_files[0])
    
    if not input_path:
        raise FileNotFoundError(f"No question paper PDF found in {class_input_dir}")
    
    output_dir = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "questionpaper.json")
    
    logger.info(f"Processing Question Paper: {input_path}")
    
    all_questions = []
    
    for page_num, text in load_pdf_pages(input_path):
        # SKIP EMPTY PAGES to avoid hallucination
        if not text or len(text.strip()) < 50:
            logger.warning(f"Page {page_num} has insufficient text ({len(text) if text else 0} chars). Skipping to avoid hallucinations.")
            continue

        logger.info(f"Processing Page {page_num}...")
        try:
            data = call_gemini_json(PHASE_1_EXTRACT_QUESTION_PROMPT, text)
            if isinstance(data, list):
                all_questions.extend(data)
            elif isinstance(data, dict):
                 # Handle case where LLM returns a single object or wrapped dict
                 if "questions" in data:
                     all_questions.extend(data["questions"])
                 else:
                     all_questions.append(data)
        except Exception as e:
            logger.error(f"Failed to extract from page {page_num}: {e}")
            raise

    # Post-process to add question_id AND DEDUPLICATE (Keep Last)
    q_map = {}
    
    for q in all_questions:
        try:
            q_num = q.get("question_number")
            if q_num:
                question_id = f"Q{q_num}"
                q["question_id"] = question_id
                
                if question_id in q_map:
                    logger.warning(f"Duplicate {question_id} detected. Overwriting previous entry.")
                
                q_map[question_id] = q
            else:
                 logger.warning(f"Skipping question without number: {q}")
        except Exception as e:
            logger.error(f"Error processing question item: {q} - {e}")
            raise

    # Convert back to list, sorted by question number
    def get_sort_key(item):
        try:
            return int(item.get("question_number", 0))
        except:
            return 9999

    final_questions = sorted(q_map.values(), key=get_sort_key)

    logger.info(f"Extracted {len(final_questions)} unique questions.")
    
    output_data = {"questions": final_questions}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    process()

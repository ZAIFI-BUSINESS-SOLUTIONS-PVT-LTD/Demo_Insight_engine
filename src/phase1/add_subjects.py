import os
import json
import logging
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def prompt_subject_ranges():
    """
    Prompts user to enter subject names and their question ranges.
    Returns a list of tuples: [(subject_name, start_q, end_q), ...]
    """
    print("\n" + "="*60)
    print("SUBJECT RANGE ASSIGNMENT")
    print("="*60)
    print("Enter subject names and their question ranges.")
    print("Example: Physics 1 45")
    print("Type 'done' when finished.\n")
    
    subjects = []
    
    while True:
        user_input = input("Enter subject and range (e.g., 'Physics 1 45') or 'done': ").strip()
        
        if user_input.lower() == 'done':
            break
        
        parts = user_input.split()
        
        if len(parts) < 3:
            print("Invalid format. Please enter: SubjectName StartQuestion EndQuestion")
            continue
        
        try:
            # Handle multi-word subject names (everything except last 2 parts)
            subject_name = ' '.join(parts[:-2])
            start_q = int(parts[-2])
            end_q = int(parts[-1])
            
            if start_q > end_q:
                print(f"Invalid range: start ({start_q}) cannot be greater than end ({end_q})")
                continue
            
            subjects.append((subject_name, start_q, end_q))
            print(f"  ✓ Added: {subject_name} (Q{start_q} - Q{end_q})")
            
        except ValueError:
            print("Invalid numbers. Please enter valid question numbers.")
            continue
    
    if not subjects:
        logger.warning("No subjects entered. Questions will have 'subject' field as 'Unknown'.")
        return []
    
    print(f"\nTotal subjects configured: {len(subjects)}")
    return subjects

def assign_subjects_to_questions(subjects_ranges):
    """
    Reads questionpaper.json, assigns subject to each question based on ranges,
    and saves the updated file.
    
    Args:
        subjects_ranges: List of tuples [(subject_name, start_q, end_q), ...]
    """
    qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")
    
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
            raise FileNotFoundError(f"Question paper JSON not found: {qp_path}")
    
    logger.info(f"Reading question paper from {qp_path}")
    
    # Load existing questionpaper.json
    with open(qp_path, 'r', encoding='utf-8') as f:
        qp_data = json.load(f)
        questions = qp_data.get("questions") if isinstance(qp_data, dict) else qp_data
    
    if not questions:
        logger.warning("No questions found in questionpaper.json")
        return
    
    # Build a lookup: question_number -> subject_name
    def get_subject_for_question(q_num):
        for subject_name, start_q, end_q in subjects_ranges:
            if start_q <= q_num <= end_q:
                return subject_name
        return "Unknown"
    
    # Add subject field to each question
    updated_count = 0
    for q in questions:
        q_num = q.get("question_number")
        if q_num:
            q["subject"] = get_subject_for_question(int(q_num))
            updated_count += 1
    
    logger.info(f"Assigned subjects to {updated_count} questions")
    
    # Save updated questionpaper.json
    output_data = {"questions": questions}
    with open(qp_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    logger.info(f"Updated questionpaper.json with subject assignments")
    
    # Print summary
    subject_counts = {}
    for q in questions:
        subj = q.get("subject", "Unknown")
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
    
    print("\nSubject assignment summary:")
    for subj, count in sorted(subject_counts.items()):
        print(f"  {subj}: {count} questions")

def process():
    """
    Main entry point: prompts user for subject ranges and updates questionpaper.json
    """
    subjects_ranges = prompt_subject_ranges()
    
    if subjects_ranges:
        assign_subjects_to_questions(subjects_ranges)
    else:
        logger.info("Skipping subject assignment (no ranges provided)")

if __name__ == "__main__":
    process()

"""
Phase 2 Data Processor
Groups merged.json data by student → subject → topic
Calculates topic metadata and separates strength/weakness questions
"""
import json
import os
from collections import defaultdict
from typing import Dict, List, Any
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def determine_correctness(correct_option: str, student_selected: str) -> str:
    """
    Determine if answer is correct, wrong, or unattempted
    Returns: 'correct', 'wrong', or 'unattempted'
    """
    if not student_selected or student_selected.strip() == "":
        return "unattempted"
    elif correct_option.strip().upper() == student_selected.strip().upper():
        return "correct"
    else:
        return "wrong"


def build_question_object(question_data: Dict) -> Dict:
    """Build clean question object for LLM input"""
    return {
        "question_id": str(question_data.get("question_id", "")),
        "question_text": question_data.get("question_text", ""),
        "options": question_data.get("options", []),
        "correct_answer": question_data.get("correct_option", ""),
        "student_selected_option": question_data.get("student_selected_option", "")
    }


def calculate_topic_metadata(topic_questions: List[Dict]) -> Dict:
    """Calculate topic-level accuracy and attempt ratio"""
    total = len(topic_questions)
    if total == 0:
        return {"topic_accuracy": 0, "attempt_ratio": 0}
    
    correct_count = sum(1 for q in topic_questions 
                       if determine_correctness(q.get("correct_option"), 
                                               q.get("student_selected_option")) == "correct")
    attempted_count = sum(1 for q in topic_questions 
                         if determine_correctness(q.get("correct_option"), 
                                                 q.get("student_selected_option")) != "unattempted")
    
    topic_accuracy = round((correct_count / total) * 100, 2) if total > 0 else 0
    attempt_ratio = round((attempted_count / total) * 100, 2) if total > 0 else 0
    
    return {
        "topic_accuracy": topic_accuracy,
        "attempt_ratio": attempt_ratio
    }


def group_by_student_subject_topic(merged_data: List[Dict], test_name: str) -> Dict[str, List[Dict]]:
    """
    Groups merged data by student_id → subject → topic
    Returns: {student_id: [subject_chunks]}
    where each subject_chunk is ready for LLM input
    """
    # First level: group by student
    student_data = defaultdict(list)
    
    for record in merged_data:
        student_id = str(record.get("student_id", ""))
        if student_id:
            student_data[student_id].append(record)
    
    logger.info(f"Grouped data for {len(student_data)} students")
    
    # Process each student
    student_subject_chunks = {}
    
    for student_id, questions in student_data.items():
        # Group by subject
        subject_data = defaultdict(list)
        for q in questions:
            subject = q.get("subject", "Unknown")
            subject_data[subject].append(q)
        
        # For each subject, group by topic
        subject_chunks = []
        
        for subject, subject_questions in subject_data.items():
            topic_data = defaultdict(list)
            for q in subject_questions:
                topic = q.get("topic", "Unknown")
                topic_data[topic].append(q)
            
            # Build topic structures
            topics = []
            for topic_name, topic_questions in topic_data.items():
                # Calculate metadata
                metadata = calculate_topic_metadata(topic_questions)
                
                # Separate into strength and weakness
                correct_questions = []
                wrong_questions = []
                unattempted_questions = []
                
                for q in topic_questions:
                    correctness = determine_correctness(
                        q.get("correct_option"), 
                        q.get("student_selected_option")
                    )
                    
                    question_obj = build_question_object(q)
                    
                    if correctness == "correct":
                        correct_questions.append(question_obj)
                    elif correctness == "wrong":
                        wrong_questions.append(question_obj)
                    else:  # unattempted
                        unattempted_questions.append(question_obj)
                
                topics.append({
                    "topic_name": topic_name,
                    "metadata": metadata,
                    "strength": {
                        "correct_questions": correct_questions
                    },
                    "weakness": {
                        "wrong_questions": wrong_questions,
                        "unattempted_questions": unattempted_questions
                    }
                })
            
            # Build subject chunk for LLM
            subject_chunk = {
                "test_name": test_name,
                "subject": subject,
                "topics": topics
            }
            
            subject_chunks.append(subject_chunk)
        
        student_subject_chunks[student_id] = subject_chunks
        logger.info(f"Student {student_id}: prepared {len(subject_chunks)} subject chunks")
    
    return student_subject_chunks


def process(target_class: str = None) -> Dict[str, List[Dict]]:
    """
    Main entry point for Phase 2 data processing
    Returns: {student_id: [subject_chunks]}
    """
    # If no class provided, ask the user to input one (use default as hint)
    if target_class is None:
        try:
            prompt = f"Enter class folder name (e.g., class_7) [{Config.DEFAULT_CLASS}]: "
            user_input = input(prompt).strip()
        except Exception:
            # If input() is not available (non-interactive), fall back to default
            user_input = ""

        target_class = user_input if user_input else Config.DEFAULT_CLASS
    
    logger.info(f"Starting Phase 2 Data Processing for {target_class}")
    
    # Load merged.json
    merged_path = os.path.join(Config.OUTPUT_DIR, target_class, "phase1", "merged.json")
    
    if not os.path.exists(merged_path):
        logger.error(f"merged.json not found at {merged_path}")
        raise FileNotFoundError(f"merged.json not found: {merged_path}")
    
    with open(merged_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    
    logger.info(f"Loaded {len(merged_data)} records from merged.json")
    
    # Extract test name from class folder name or use default
    test_name = target_class.replace("class_", "").replace("_", " ").title()
    
    # Group and structure data
    student_chunks = group_by_student_subject_topic(merged_data, test_name)
    
    logger.info(f"Data processing complete: {len(student_chunks)} students ready for LLM analysis")
    
    return student_chunks


if __name__ == "__main__":
    chunks = process()
    # Print sample for verification
    sample_student = list(chunks.keys())[0]
    print(f"\nSample student {sample_student}:")
    print(json.dumps(chunks[sample_student][0], indent=2))

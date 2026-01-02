"""
Phase 5 Data Processor
Filters wrong questions and groups by topic with comprehensive metrics
"""
import json
import os
from typing import Dict, List
from collections import defaultdict
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def is_wrong_question(record: Dict) -> bool:
    """
    Determines if a question was answered incorrectly
    
    Args:
        record: Merged data record
    
    Returns:
        True if wrong or unattempted
    """
    correct = str(record.get("correct_option", "")).strip().upper()
    selected = str(record.get("student_selected_option", "")).strip().upper()
    
    # Consider both wrong answers and unattempted as "wrong"
    return selected != correct or not selected


def calculate_topic_metrics(all_questions: List[Dict], wrong_questions: List[Dict]) -> Dict:
    """
    Calculate comprehensive metrics for a topic
    
    Args:
        all_questions: All questions in this topic
        wrong_questions: Wrong questions in this topic
    
    Returns:
        Dict with accuracy, weighted_accuracy, total_questions
    """
    total = len(all_questions)
    wrong_count = len(wrong_questions)
    correct_count = total - wrong_count
    
    accuracy = round((correct_count / total) * 100, 2) if total > 0 else 0
    
    # Weighted accuracy: accuracy weighted by question count
    # Higher question count = more weight
    weight = total / 100  # Normalize weight
    weighted_accuracy = round(accuracy * weight, 2)
    
    return {
        "accuracy": accuracy,
        "weighted_accuracy": weighted_accuracy,
        "total_questions": total,
        "correct_count": correct_count,
        "wrong_count": wrong_count
    }


def group_by_topic(student_records: List[Dict]) -> Dict[str, Dict]:
    """
    Groups student records by topic and filters wrong questions
    
    Args:
        student_records: All records for a student
    
    Returns:
        Dict[topic_name, {metadata, wrong_questions}]
    """
    # First group all questions by topic
    topic_all_questions = defaultdict(list)
    topic_info = {}  # Store chapter and subject
    
    for record in student_records:
        topic = record.get("topic", "Unknown")
        topic_all_questions[topic].append(record)
        
        # Store topic metadata (chapter, subject)
        if topic not in topic_info:
            topic_info[topic] = {
                "chapter": record.get("chapter", "Unknown"),
                "subject": record.get("subject", "Unknown")
            }
    
    # Now filter only wrong questions and calculate metrics
    topic_groups = {}
    
    for topic, all_questions in topic_all_questions.items():
        # Filter wrong questions
        wrong_questions = [q for q in all_questions if is_wrong_question(q)]
        
        # Skip topics with no wrong questions
        if not wrong_questions:
            continue
        
        # Calculate metrics
        metrics = calculate_topic_metrics(all_questions, wrong_questions)
        
        # Build wrong question details
        wrong_question_details = []
        for q in wrong_questions:
            wrong_question_details.append({
                "question_id": q.get("question_id"),
                "question_text": q.get("question_text", ""),
                "options_map": q.get("options_map", {}),
                "correct_option": q.get("correct_option", ""),
                "student_selected_option": q.get("student_selected_option", ""),
                "test_name": q.get("test_name", "Unknown")
            })
        
        topic_groups[topic] = {
            "topic_name": topic,
            "chapter": topic_info[topic]["chapter"],
            "subject": topic_info[topic]["subject"],
            "accuracy": metrics["accuracy"],
            "weighted_accuracy": metrics["weighted_accuracy"],
            "total_questions": metrics["total_questions"],
            "correct_count": metrics["correct_count"],
            "wrong_count": metrics["wrong_count"],
            "wrong_questions": wrong_question_details
        }
    
    return topic_groups


def load_student_data(student_id: str) -> List[Dict]:
    """
    Loads student data from phase4 output
    
    Args:
        student_id: Student identifier
    
    Returns:
        List of all records for this student
    """
    student_path = os.path.join(Config.OUTPUT_DIR, "phase4", "students", f"{student_id}.json")
    
    if not os.path.exists(student_path):
        logger.warning(f"Student file not found: {student_id}.json")
        return []
    
    try:
        with open(student_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        records = data.get("records", [])
        logger.info(f"Loaded {len(records)} records for student {student_id}")
        return records
    except Exception as e:
        logger.error(f"Failed to load student {student_id}: {e}")
        return []


def process_all_students() -> Dict[str, Dict]:
    """
    Process all students from phase4 output
    
    Returns:
        Dict[student_id, topic_groups]
    """
    students_dir = os.path.join(Config.OUTPUT_DIR, "phase4", "students")
    
    if not os.path.exists(students_dir):
        logger.error(f"Phase4 students directory not found: {students_dir}")
        return {}
    
    student_files = [f for f in os.listdir(students_dir) 
                     if f.endswith('.json') and f != '_index.json']
    
    if not student_files:
        logger.warning(f"No student files found in {students_dir}")
        return {}
    
    logger.info(f"Found {len(student_files)} student files")
    
    all_student_data = {}
    
    for filename in student_files:
        student_id = filename.replace('.json', '')
        
        # Load student records
        records = load_student_data(student_id)
        
        if not records:
            logger.warning(f"No records for student {student_id}, skipping")
            continue
        
        # Group by topic and filter wrong questions
        topic_groups = group_by_topic(records)
        
        if not topic_groups:
            logger.info(f"Student {student_id} has no weak topics (all correct!)")
            continue
        
        all_student_data[student_id] = topic_groups
        logger.info(f"Student {student_id}: {len(topic_groups)} weak topics identified")
    
    logger.info(f"Processed {len(all_student_data)} students with weak topics")
    return all_student_data


def process() -> Dict[str, Dict]:
    """
    Main entry point for Phase 5 data processing
    
    Returns:
        Dict[student_id, Dict[topic_name, topic_data]]
    """
    logger.info("Starting Phase 5 Data Processing")
    
    student_data = process_all_students()
    
    if not student_data:
        logger.error("No student data with weak topics found. Phase 5 cannot proceed.")
        return {}
    
    logger.info(f"Data processing complete: {len(student_data)} students ready for analysis")
    
    return student_data


if __name__ == "__main__":
    data = process()
    
    if data:
        # Print sample
        sample_student = list(data.keys())[0]
        sample_topic = list(data[sample_student].keys())[0]
        print(f"\nSample: Student {sample_student}, Topic: {sample_topic}")
        print(json.dumps(data[sample_student][sample_topic], indent=2)[:1000])

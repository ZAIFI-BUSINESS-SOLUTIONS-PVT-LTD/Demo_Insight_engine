"""
Phase 3 Data Aggregator
Reads all student JSON files and groups data topic-wise across all tests
"""
import json
import os
from typing import Dict, List
from collections import defaultdict
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def group_by_topic(student_data: Dict) -> Dict[str, List[Dict]]:
    """
    Groups a student's insights by topic across all tests
    
    Args:
        student_data: Student JSON data with insights list
    
    Returns:
        Dict[topic_name, list_of_test_records]
    """
    topic_groups = defaultdict(list)
    
    insights = student_data.get("insights", [])
    
    for insight in insights:
        topic_name = insight.get("topic_name", "Unknown")
        
        # Extract relevant data for pattern analysis
        topic_record = {
            "test_name": insight.get("test_name", "Unknown"),
            "subject": insight.get("subject", "Unknown"),
            "topic_accuracy": insight.get("topic_metadata", {}).get("topic_accuracy", 0),
            "attempt_ratio": insight.get("topic_metadata", {}).get("attempt_ratio", 0),
            "question_count": insight.get("topic_metadata", {}).get("question_count", 0),
            "strength_insights": insight.get("strength_insights", []),
            "weakness_insights": insight.get("weakness_insights", []),
            "learning_recommendations": insight.get("learning_recommendations", [])
        }
        
        topic_groups[topic_name].append(topic_record)
    
    return dict(topic_groups)


def load_all_students() -> Dict[str, Dict]:
    """
    Loads all student JSON files from output/students/
    
    Returns:
        Dict[student_id, grouped_topic_data]
    """
    students_dir = os.path.join(Config.OUTPUT_DIR, "students")
    
    if not os.path.exists(students_dir):
        logger.error(f"Students directory not found: {students_dir}")
        return {}
    
    student_files = [f for f in os.listdir(students_dir) 
                     if f.endswith('.json') and f != '_index.json']
    
    if not student_files:
        logger.warning(f"No student JSON files found in {students_dir}")
        return {}
    
    logger.info(f"Found {len(student_files)} student files")
    
    all_students = {}
    
    for filename in student_files:
        filepath = os.path.join(students_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                student_data = json.load(f)
            
            student_id = student_data.get("student_id", filename.replace('.json', ''))
            
            # Group by topic
            topic_grouped = group_by_topic(student_data)
            
            if topic_grouped:
                all_students[student_id] = topic_grouped
                logger.info(f"Loaded student {student_id}: {len(topic_grouped)} topics")
            else:
                logger.warning(f"Student {student_id} has no topic data")
                
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            continue
    
    logger.info(f"Successfully loaded {len(all_students)} students with topic-grouped data")
    return all_students


def process() -> Dict[str, Dict]:
    """
    Main entry point for Phase 3 data aggregation
    
    Returns:
        Dict[student_id, Dict[topic_name, List[test_records]]]
    """
    logger.info("Starting Phase 3 Data Aggregation")
    
    student_data = load_all_students()
    
    if not student_data:
        logger.error("No student data loaded. Phase 3 cannot proceed.")
        return {}
    
    logger.info(f"Data aggregation complete: {len(student_data)} students ready for analysis")
    
    return student_data


if __name__ == "__main__":
    data = process()
    
    if data:
        # Print sample
        sample_student = list(data.keys())[0]
        sample_topic = list(data[sample_student].keys())[0]
        print(f"\nSample: Student {sample_student}, Topic: {sample_topic}")
        print(json.dumps(data[sample_student][sample_topic], indent=2))

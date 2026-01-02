"""
Phase 2 Output Writer
Writes student-level JSON files (global, not tied to class/phase/batch structure)
"""
import json
import os
from typing import Dict, List
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def write_student_output(student_id: str, insights: List[Dict], target_class: str = None):
    """
    Writes a single student's insights to a JSON file
    Merges with existing file: keeps existing test+topic entries, appends new ones
    File location: output/students/{student_id}.json (global)
    """
    # Create global student output directory
    students_dir = os.path.join(Config.OUTPUT_DIR, "students")
    os.makedirs(students_dir, exist_ok=True)
    
    output_path = os.path.join(students_dir, f"{student_id}.json")
    
    # Load existing insights if file exists
    existing_insights = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_insights = existing_data.get("insights", [])
        except Exception as e:
            logger.warning(f"Could not load existing file for student {student_id}: {e}. Will overwrite.")
            existing_insights = []
    
    # Build set of existing (test_name, topic_name) keys
    existing_keys = set()
    for insight in existing_insights:
        key = (insight.get("test_name", ""), insight.get("topic_name", ""))
        existing_keys.add(key)
    
    # Filter new insights: only append if (test_name, topic_name) not in existing
    new_count = 0
    for insight in insights:
        key = (insight.get("test_name", ""), insight.get("topic_name", ""))
        if key not in existing_keys:
            existing_insights.append(insight)
            existing_keys.add(key)
            new_count += 1
    
    # Write merged data
    output_data = {
        "student_id": student_id,
        "insights": existing_insights
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote output for student {student_id}: {new_count} new insights appended, {len(existing_insights)} total")


def write_index_file(student_ids: List[str], target_class: str = None):
    """
    Writes the index file summarizing all processed students
    """
    students_dir = os.path.join(Config.OUTPUT_DIR, "students")
    os.makedirs(students_dir, exist_ok=True)
    
    index_path = os.path.join(students_dir, "_index.json")
    
    index_data = {
        "total_students": len(student_ids),
        "student_ids": student_ids,
        "class": target_class or Config.DEFAULT_CLASS
    }
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    
    logger.info(f"Wrote index file: {index_path} with {len(student_ids)} students")


def process(all_results: Dict[str, List[Dict]], target_class: str = None):
    """
    Writes all student results to individual JSON files (batch mode)
    """
    logger.info(f"Writing outputs for {len(all_results)} students")
    
    for student_id, insights in all_results.items():
        write_student_output(student_id, insights, target_class)
    
    logger.info(f"Successfully wrote {len(all_results)} student output files")
    
    # Write index file
    write_index_file(list(all_results.keys()), target_class)


if __name__ == "__main__":
    # For testing
    from src.phase2.data_processor import process as process_data
    from src.phase2.llm_analyzer import process as process_llm
    
    student_chunks = process_data()
    results = process_llm(student_chunks)
    process(results)

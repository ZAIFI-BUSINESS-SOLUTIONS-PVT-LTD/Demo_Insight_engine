"""
Phase 4 Aggregator
Aggregates student data across multiple classes/tests from merged.json files
Creates student-wise JSON with all question records from all selected tests
"""
import json
import os
from typing import Dict, List
from collections import defaultdict
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def discover_available_classes() -> List[str]:
    """
    Discover classes that have phase1/merged.json
    
    Returns:
        List of class folder names
    """
    available = []
    
    if not os.path.exists(Config.OUTPUT_DIR):
        return available
    
    for folder in os.listdir(Config.OUTPUT_DIR):
        folder_path = os.path.join(Config.OUTPUT_DIR, folder)
        merged_path = os.path.join(folder_path, "phase1", "merged.json")
        
        if os.path.isdir(folder_path) and os.path.exists(merged_path):
            available.append(folder)
    
    return available


def prompt_for_classes() -> List[str]:
    """
    Prompts user to select classes for aggregation
    
    Returns:
        List of selected class folder names
    """
    available = discover_available_classes()
    
    if not available:
        logger.error("No classes with phase1/merged.json found.")
        return []
    
    print("\n" + "="*60)
    print("PHASE 4: MULTI-TEST STUDENT AGGREGATION")
    print("="*60)
    print(f"Available classes: {', '.join(available)}")
    print("\nEnter class names separated by commas (e.g., class_7, class_8)")
    print("Or enter 'all' to include all available classes\n")
    
    try:
        user_input = input("Enter classes: ").strip()
    except Exception:
        logger.error("Input not available. Running non-interactively.")
        return []
    
    if not user_input:
        logger.error("No classes entered.")
        return []
    
    if user_input.lower() == 'all':
        selected = available
    else:
        # Parse comma-separated list
        selected = [c.strip() for c in user_input.split(',')]
        # Validate
        invalid = [c for c in selected if c not in available]
        if invalid:
            logger.error(f"Invalid classes: {', '.join(invalid)}")
            return []
    
    logger.info(f"Selected classes: {', '.join(selected)}")
    print(f"\n✓ Selected {len(selected)} classes for aggregation")
    
    return selected


def load_merged_data(class_name: str) -> List[Dict]:
    """
    Loads merged.json for a specific class
    
    Args:
        class_name: Class folder name
    
    Returns:
        List of merged records
    """
    merged_path = os.path.join(Config.OUTPUT_DIR, class_name, "phase1", "merged.json")
    
    if not os.path.exists(merged_path):
        logger.warning(f"merged.json not found for {class_name}")
        return []
    
    try:
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} records from {class_name}")
        return data
    except Exception as e:
        logger.error(f"Failed to load merged.json for {class_name}: {e}")
        return []


def aggregate_by_student(selected_classes: List[str]) -> Dict[str, List[Dict]]:
    """
    Aggregates all merged records by student across selected classes
    
    Args:
        selected_classes: List of class folder names
    
    Returns:
        Dict[student_id, list_of_all_records_with_test_name]
    """
    student_records = defaultdict(list)
    
    for class_name in selected_classes:
        logger.info(f"Processing {class_name}...")
        
        merged_data = load_merged_data(class_name)
        
        if not merged_data:
            logger.warning(f"Skipping {class_name} (no data)")
            continue
        
        # Add test_name and group by student
        for record in merged_data:
            student_id = str(record.get("student_id", ""))
            
            if not student_id:
                logger.warning(f"Record without student_id in {class_name}, skipping")
                continue
            
            # Add test_name field (use class name as test identifier)
            record_with_test = record.copy()
            record_with_test["test_name"] = class_name
            
            student_records[student_id].append(record_with_test)
    
    return dict(student_records)


def write_student_files(student_data: Dict[str, List[Dict]]):
    """
    Writes individual student JSON files to output/phase4/students/
    
    Args:
        student_data: Dict[student_id, list_of_records]
    """
    output_dir = os.path.join(Config.OUTPUT_DIR, "phase4", "students")
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Writing {len(student_data)} student files...")
    
    for student_id, records in student_data.items():
        output_path = os.path.join(output_dir, f"{student_id}.json")
        
        student_json = {
            "student_id": student_id,
            "total_records": len(records),
            "records": records
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(student_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote {student_id}.json with {len(records)} records")
    
    logger.info(f"Successfully wrote {len(student_data)} student files")


def write_index_file(student_data: Dict[str, List[Dict]], selected_classes: List[str]):
    """
    Writes index file with summary information
    
    Args:
        student_data: Dict[student_id, list_of_records]
        selected_classes: List of class names included
    """
    output_dir = os.path.join(Config.OUTPUT_DIR, "phase4", "students")
    os.makedirs(output_dir, exist_ok=True)
    
    index_path = os.path.join(output_dir, "_index.json")
    
    index_data = {
        "total_students": len(student_data),
        "student_ids": sorted(list(student_data.keys())),
        "classes_included": selected_classes,
        "records_per_student": {
            student_id: len(records) 
            for student_id, records in student_data.items()
        }
    }
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    
    logger.info(f"Wrote index file: {index_path}")


def process() -> Dict[str, List[Dict]]:
    """
    Main entry point for Phase 4 aggregation
    
    Returns:
        Dict[student_id, list_of_records]
    """
    logger.info("Starting Phase 4: Multi-Test Student Aggregation")
    
    # Step 1: Prompt for classes
    selected_classes = prompt_for_classes()
    
    if not selected_classes:
        logger.error("No classes selected. Phase 4 cannot proceed.")
        return {}
    
    # Step 2: Aggregate data by student
    logger.info(f"Aggregating data from {len(selected_classes)} classes...")
    student_data = aggregate_by_student(selected_classes)
    
    if not student_data:
        logger.error("No student data found. Phase 4 cannot proceed.")
        return {}
    
    # Step 3: Count unique students
    unique_count = len(student_data)
    logger.info(f"Found {unique_count} unique students across selected classes")
    print(f"\n✓ Found {unique_count} unique students")
    
    # Step 4: Write student files
    write_student_files(student_data)
    
    # Step 5: Write index
    write_index_file(student_data, selected_classes)
    
    logger.info(f"Phase 4 aggregation complete: {unique_count} students processed")
    
    return student_data


if __name__ == "__main__":
    data = process()
    
    if data:
        # Print sample
        sample_student = list(data.keys())[0]
        print(f"\nSample: Student {sample_student}")
        print(f"Total records: {len(data[sample_student])}")
        print(f"First record preview:")
        print(json.dumps(data[sample_student][0], indent=2)[:500])

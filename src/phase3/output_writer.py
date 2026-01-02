"""
Phase 3 Output Writer
Writes pattern analysis insights to individual student files and summary CSV
"""
import json
import os
import csv
from typing import Dict, List
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def write_student_insights(student_id: str, insights: List[Dict]):
    """
    Writes Phase 3 insights to student's JSON file
    Adds a 'pattern_insights' field without overwriting existing Phase 2 data
    
    Args:
        student_id: Student identifier
        insights: List of 5 insight dictionaries
    """
    students_dir = os.path.join(Config.OUTPUT_DIR, "students")
    os.makedirs(students_dir, exist_ok=True)
    
    output_path = os.path.join(students_dir, f"{student_id}.json")
    
    # Load existing student data
    student_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                student_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing data for student {student_id}: {e}")
            student_data = {"student_id": student_id}
    else:
        student_data = {"student_id": student_id}
    
    # Add pattern insights (Phase 3 data)
    student_data["pattern_insights"] = insights
    
    # Write updated data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(student_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wrote pattern insights for student {student_id}")


def write_summary_csv(all_insights: Dict[str, List[Dict]]):
    """
    Writes a summary CSV with all students' top 5 insights
    
    Args:
        all_insights: Dict[student_id, list_of_5_insights]
    """
    output_dir = os.path.join(Config.OUTPUT_DIR, "phase3")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "student_pattern_insights.csv")
    
    # CSV structure: student_id, insight_rank, insight, recommendation, citation
    rows = []
    
    for student_id, insights in all_insights.items():
        for rank, insight_data in enumerate(insights, 1):
            rows.append({
                "student_id": student_id,
                "insight_rank": rank,
                "insight": insight_data.get("insight", ""),
                "recommendation": insight_data.get("recommendation", ""),
                "citation": insight_data.get("citation", "")
            })
    
    # Write CSV
    if rows:
        fieldnames = ["student_id", "insight_rank", "insight", "recommendation", "citation"]
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Wrote summary CSV: {output_path} with {len(rows)} rows")
    else:
        logger.warning("No insights to write to CSV")


def process(all_insights: Dict[str, List[Dict]]):
    """
    Main entry point for Phase 3 output writing
    
    Args:
        all_insights: Dict[student_id, list_of_5_insights]
    """
    logger.info(f"Writing Phase 3 outputs for {len(all_insights)} students")
    
    # Write individual student files
    for student_id, insights in all_insights.items():
        write_student_insights(student_id, insights)
    
    # Write summary CSV
    write_summary_csv(all_insights)
    
    logger.info(f"Phase 3 output writing complete")


if __name__ == "__main__":
    from src.phase3.data_aggregator import process as aggregate_data
    from src.phase3.llm_analyzer import process as analyze_patterns
    
    student_data = aggregate_data()
    if student_data:
        insights = analyze_patterns(student_data)
        process(insights)
        print(f"\nPhase 3 complete: {len(insights)} students processed")

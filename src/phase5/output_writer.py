"""
Phase 5 Output Writer
Writes unified pattern insights to student files and summary CSV
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
    Writes Phase 5 insights to student's JSON file in phase4
    Adds 'phase5_insights' field without overwriting existing data
    
    Args:
        student_id: Student identifier
        insights: List of 5 insight pairs (problem + action + citation)
    """
    student_path = os.path.join(Config.OUTPUT_DIR, "phase4", "students", f"{student_id}.json")
    
    if not os.path.exists(student_path):
        logger.warning(f"Student file not found for {student_id}, skipping")
        return
    
    try:
        # Load existing data
        with open(student_path, 'r', encoding='utf-8') as f:
            student_data = json.load(f)
        
        # Add phase5 insights
        student_data["phase5_insights"] = insights
        
        # Write back
        with open(student_path, 'w', encoding='utf-8') as f:
            json.dump(student_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote Phase 5 insights for student {student_id}")
        
    except Exception as e:
        logger.error(f"Failed to write insights for student {student_id}: {e}")


def write_insights_json(all_insights: Dict[str, List[Dict]]):
    """
    Writes unified insights summary JSON
    
    Args:
        all_insights: Dict[student_id, list_of_5_insights]
    """
    output_dir = os.path.join(Config.OUTPUT_DIR, "phase5")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "student_pattern_insights.json")
    
    # Build structured output
    output_data = []
    
    for student_id, insights in all_insights.items():
        for rank, insight in enumerate(insights, 1):
            output_data.append({
                "student_id": student_id,
                "insight_rank": rank,
                "topic": insight.get("topic", ""),
                "subject": insight.get("subject", ""),
                "accuracy": insight.get("accuracy", 0),
                "problem": insight.get("problem", ""),
                "action": insight.get("action", ""),
                "citation": insight.get("citation", "")
            })
    
    if output_data:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wrote insights JSON: {output_path} with {len(output_data)} insights")
    else:
        logger.warning("No insights to write to JSON")


def process(all_insights: Dict[str, List[Dict]]):
    """
    Main entry point for Phase 5 output writing
    
    Args:
        all_insights: Dict[student_id, list_of_5_insights]
    """
    logger.info(f"Writing Phase 5 outputs for {len(all_insights)} students")
    
    # Write individual student files
    for student_id, insights in all_insights.items():
        write_student_insights(student_id, insights)
    
    # Write summary JSON
    write_insights_json(all_insights)
    
    logger.info(f"Phase 5 output writing complete")


if __name__ == "__main__":
    from src.phase5.data_processor import process as process_data
    from src.phase5.llm_analyzer import process as analyze
    
    student_data = process_data()
    if student_data:
        insights = analyze(student_data)
        process(insights)
        print(f"\nPhase 5 complete: {len(insights)} students processed")

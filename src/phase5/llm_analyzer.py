"""
Phase 5 LLM Analyzer
Generates unified pattern insights (problem + action + citation pairs)
One LLM call per student
"""
import json
import time
from typing import Dict, List, Any
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.utils.logger import setup_logger
from src.prompts import PHASE_5_UNIFIED_INSIGHTS_PROMPT

logger = setup_logger(__name__)


def validate_insights(response: Any, student_id: str) -> List[Dict]:
    """
    Validates unified insights response (expects exactly 5 items)
    
    Each item must have: topic, subject, accuracy, problem, action, citation
    """
    if isinstance(response, dict) and "insights" in response:
        response = response["insights"]
    
    if not isinstance(response, list):
        logger.error(f"Student {student_id}: Expected list for insights, got {type(response)}")
        return []
    
    required_fields = ["topic", "subject", "accuracy", "problem", "action", "citation"]
    validated = []
    
    for i, item in enumerate(response):
        if not isinstance(item, dict):
            logger.warning(f"Student {student_id}: Insight {i} is not a dict")
            continue
        
        missing = [f for f in required_fields if f not in item]
        if missing:
            logger.warning(f"Student {student_id}: Insight {i} missing fields: {missing}")
            continue
        
        # Ensure types
        item["topic"] = str(item.get("topic", "")).strip()
        item["subject"] = str(item.get("subject", "")).strip()
        item["problem"] = str(item.get("problem", "")).strip()
        item["action"] = str(item.get("action", "")).strip()
        item["citation"] = str(item.get("citation", "")).strip()
        
        try:
            item["accuracy"] = float(item.get("accuracy", 0))
        except:
            item["accuracy"] = 0.0
        
        validated.append(item)
    
    # Ensure exactly 5 items
    if len(validated) < 5:
        logger.warning(f"Student {student_id}: Only {len(validated)} insights, padding to 5")
        while len(validated) < 5:
            validated.append({
                "topic": "General",
                "subject": "Overall",
                "accuracy": 0.0,
                "problem": f"Additional pattern analysis needed",
                "action": f"Continue monitoring performance across tests",
                "citation": "Insufficient data for pattern detection"
            })
    elif len(validated) > 5:
        logger.warning(f"Student {student_id}: {len(validated)} insights, truncating to 5")
        validated = validated[:5]
    
    return validated


def generate_insights(student_id: str, topic_data: Dict) -> List[Dict]:
    """
    Generates unified pattern insights for a student (5 pairs)
    
    Args:
        student_id: Student identifier
        topic_data: Dict of topic-wise weak performance data
    
    Returns:
        List of 5 insight pairs (problem + action + citation)
    """
    logger.info(f"Generating pattern insights for student {student_id} with {len(topic_data)} weak topics")
    
    try:
        # Prepare content
        content = json.dumps(topic_data, indent=2, ensure_ascii=False)
        
        # Call LLM (single call)
        response = call_gemini_json(PHASE_5_UNIFIED_INSIGHTS_PROMPT, content)
        
        # Validate
        validated = validate_insights(response, student_id)
        
        if len(validated) != 5:
            logger.error(f"Student {student_id}: Failed to get exactly 5 insights")
            # Fallback
            fallback = []
            for i in range(5):
                fallback.append({
                    "topic": "General",
                    "subject": "Overall",
                    "accuracy": 0.0,
                    "problem": f"Pattern analysis incomplete",
                    "action": f"Review weak topics and practice with focused effort",
                    "citation": "Error during pattern detection"
                })
            return fallback
        
        logger.info(f"Successfully generated 5 pattern insights for student {student_id}")
        return validated
        
    except Exception as e:
        logger.error(f"Error generating insights for student {student_id}: {e}")
        # Fallback
        fallback = []
        for i in range(5):
            fallback.append({
                "topic": "General",
                "subject": "Overall",
                "accuracy": 0.0,
                "problem": f"Error during pattern analysis",
                "action": f"Review performance data and practice weak topics systematically",
                "citation": f"Analysis error: {str(e)[:50]}"
            })
        return fallback


def process(student_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Process all students to generate unified pattern insights
    
    Args:
        student_data: Dict[student_id, topic_data]
    
    Returns:
        Dict[student_id, list_of_5_insights]
    """
    setup_gemini()
    
    total_students = len(student_data)
    logger.info(f"Starting Phase 5 LLM analysis for {total_students} students")
    
    all_insights = {}
    
    for idx, (student_id, topic_data) in enumerate(student_data.items(), 1):
        logger.info(f"[{idx}/{total_students}] Processing student {student_id}")
        
        # Generate insights (single LLM call)
        insights = generate_insights(student_id, topic_data)
        
        all_insights[student_id] = insights
        
        # Rate limiting
        time.sleep(1)
        
        logger.info(f"Completed student {student_id}: 5 insight pairs")
    
    logger.info(f"Phase 5 LLM analysis complete for all {total_students} students")
    
    return all_insights


if __name__ == "__main__":
    from src.phase5.data_processor import process as process_data
    
    student_data = process_data()
    if student_data:
        insights = process(student_data)
        
        # Print sample
        sample_student = list(insights.keys())[0]
        print(f"\nSample insights for student {sample_student}:")
        print(json.dumps(insights[sample_student], indent=2))

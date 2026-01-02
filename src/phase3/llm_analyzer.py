"""
Phase 3 LLM Analyzer
Analyzes topic-wise patterns across tests for each student
One LLM call per student to identify top 5 actionable insights
"""
import json
import time
from typing import Dict, List, Any
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.utils.logger import setup_logger
from src.prompts import PHASE_3_PATTERN_ANALYSIS_PROMPT

logger = setup_logger(__name__)


def validate_and_repair_insights(response: Any, student_id: str) -> List[Dict]:
    """
    Validates LLM response and repairs if needed
    Expected: list of exactly 5 insights
    Each insight must have: insight, recommendation, citation
    """
    # Ensure response is a list
    if isinstance(response, dict):
        # Check if wrapped in a key
        if "insights" in response:
            response = response["insights"]
        else:
            # Single insight, wrap in list
            response = [response]
    
    if not isinstance(response, list):
        logger.error(f"Student {student_id}: Expected list response, got {type(response)}")
        return []
    
    # Validate each insight
    required_fields = ["insight", "recommendation", "citation"]
    validated = []
    
    for i, item in enumerate(response):
        if not isinstance(item, dict):
            logger.warning(f"Student {student_id}: Insight {i} is not a dict, skipping")
            continue
        
        # Check required fields
        missing = [f for f in required_fields if f not in item or not item[f]]
        if missing:
            logger.warning(f"Student {student_id}: Insight {i} missing fields: {missing}")
            # Fill with fallbacks
            if "insight" not in item or not item["insight"]:
                item["insight"] = f"Pattern analysis incomplete for insight {i+1}"
            if "recommendation" not in item or not item["recommendation"]:
                item["recommendation"] = "Review performance data manually"
            if "citation" not in item or not item["citation"]:
                item["citation"] = "Insufficient data"
        
        # Ensure strings
        item["insight"] = str(item.get("insight", "")).strip()
        item["recommendation"] = str(item.get("recommendation", "")).strip()
        item["citation"] = str(item.get("citation", "")).strip()
        
        validated.append(item)
    
    # Ensure exactly 5 insights
    if len(validated) < 5:
        logger.warning(f"Student {student_id}: Only {len(validated)} insights returned, padding to 5")
        while len(validated) < 5:
            validated.append({
                "insight": f"Additional pattern analysis needed (insight {len(validated)+1})",
                "recommendation": "Continue monitoring performance across topics",
                "citation": "Insufficient data for pattern detection"
            })
    elif len(validated) > 5:
        logger.warning(f"Student {student_id}: {len(validated)} insights returned, truncating to top 5")
        validated = validated[:5]
    
    return validated


def analyze_student_patterns(student_id: str, topic_data: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Sends one student's topic-grouped data to LLM for pattern analysis
    
    Args:
        student_id: Student identifier
        topic_data: Dict[topic_name, list_of_test_records]
    
    Returns:
        List of exactly 5 insight dictionaries
    """
    logger.info(f"Analyzing patterns for student {student_id} with {len(topic_data)} topics")
    
    try:
        # Prepare content for LLM
        content = json.dumps(topic_data, indent=2, ensure_ascii=False)
        
        # Call LLM
        response = call_gemini_json(PHASE_3_PATTERN_ANALYSIS_PROMPT, content)
        
        # Validate and repair
        validated_insights = validate_and_repair_insights(response, student_id)
        
        if len(validated_insights) != 5:
            logger.error(f"Student {student_id}: Failed to get exactly 5 insights after repair")
            # Create fallback insights
            fallback = []
            for i in range(5):
                fallback.append({
                    "insight": f"Pattern analysis incomplete for student {student_id}",
                    "recommendation": "Manual review of performance data recommended",
                    "citation": "Analysis error occurred"
                })
            return fallback
        
        logger.info(f"Successfully analyzed student {student_id}: 5 insights generated")
        return validated_insights
        
    except Exception as e:
        logger.error(f"Error analyzing student {student_id}: {e}")
        # Return fallback
        fallback = []
        for i in range(5):
            fallback.append({
                "insight": f"Analysis failed for student {student_id}",
                "recommendation": "Please review performance data manually",
                "citation": f"Error: {str(e)[:50]}"
            })
        return fallback


def process(student_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
    """
    Process all students' topic data through LLM for pattern analysis
    
    Args:
        student_data: Dict[student_id, Dict[topic_name, test_records]]
    
    Returns:
        Dict[student_id, list_of_5_insights]
    """
    setup_gemini()
    
    total_students = len(student_data)
    logger.info(f"Starting Phase 3 LLM analysis for {total_students} students")
    
    all_insights = {}
    
    for idx, (student_id, topic_data) in enumerate(student_data.items(), 1):
        logger.info(f"[{idx}/{total_students}] Processing student {student_id}")
        
        # Analyze this student (one LLM call)
        insights = analyze_student_patterns(student_id, topic_data)
        
        all_insights[student_id] = insights
        
        # Rate limiting
        time.sleep(1)
        
        logger.info(f"Completed student {student_id}: {len(insights)} insights")
    
    logger.info(f"Phase 3 LLM analysis complete for all {total_students} students")
    
    return all_insights


if __name__ == "__main__":
    from src.phase3.data_aggregator import process as aggregate_data
    
    student_data = aggregate_data()
    if student_data:
        insights = process(student_data)
        
        # Print sample
        sample_student = list(insights.keys())[0]
        print(f"\nSample insights for student {sample_student}:")
        print(json.dumps(insights[sample_student], indent=2))

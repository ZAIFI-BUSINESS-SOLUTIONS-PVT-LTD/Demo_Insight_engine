"""
Phase 2 LLM Analyzer
Sends subject chunks to LLM and processes responses
"""
import json
import time
from typing import List, Dict, Any
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.utils.logger import setup_logger
from src.prompts import PHASE_2_NEW_ANALYSIS_PROMPT
from src.phase2.output_writer import write_student_output

logger = setup_logger(__name__)


def validate_and_repair_response(response: Any, subject_chunk: Dict) -> List[Dict]:
    """
    Validates LLM response and repairs if needed
    Returns list of topic insights
    """
    # Ensure response is a list
    if isinstance(response, dict):
        # If single topic response, wrap in list
        if "topic_name" in response:
            response = [response]
        else:
            logger.warning("Invalid response structure, expected list or topic dict")
            return []
    
    if not isinstance(response, list):
        logger.warning(f"Expected list response, got {type(response)}")
        return []
    
    # Expected fields
    required_fields = ["test_name", "subject", "topic_name", 
                      "strength_insights", "weakness_insights", "learning_recommendations"]
    
    validated = []
    topics_from_input = [t["topic_name"] for t in subject_chunk.get("topics", [])]
    
    for i, item in enumerate(response):
        if not isinstance(item, dict):
            logger.warning(f"Topic item {i} is not a dict, skipping")
            continue
        
        # Check required fields
        missing = [f for f in required_fields if f not in item]
        if missing:
            logger.warning(f"Topic {i} missing fields: {missing}")
            # Fill with fallbacks
            for field in missing:
                if field == "test_name":
                    item["test_name"] = subject_chunk.get("test_name", "Unknown")
                elif field == "subject":
                    item["subject"] = subject_chunk.get("subject", "Unknown")
                elif field == "topic_name":
                    item["topic_name"] = topics_from_input[i] if i < len(topics_from_input) else f"Topic_{i+1}"
                elif field in ["strength_insights", "weakness_insights", "learning_recommendations"]:
                    item[field] = ["Insufficient data available to generate meaningful insights."]
        
        # Ensure arrays
        for field in ["strength_insights", "weakness_insights", "learning_recommendations"]:
            if field in item and not isinstance(item[field], list):
                item[field] = [str(item[field])]
            elif field not in item:
                item[field] = ["Data unavailable."]
        
        validated.append(item)
    
    return validated


def analyze_subject_chunk(subject_chunk: Dict, student_id: str) -> List[Dict]:
    """
    Sends one subject chunk to LLM and returns topic insights with metadata
    """
    subject = subject_chunk.get("subject", "Unknown")
    logger.info(f"Analyzing {subject} for student {student_id}...")
    
    # Extract metadata map: topic_name -> metadata
    metadata_map = {}
    for topic in subject_chunk.get("topics", []):
        topic_name = topic.get("topic_name", "Unknown")
        metadata_map[topic_name] = topic.get("metadata", {})
    
    try:
        # Prepare content
        content = json.dumps(subject_chunk, indent=2)
        
        # Call LLM
        response = call_gemini_json(PHASE_2_NEW_ANALYSIS_PROMPT, content)
        
        # Validate and repair
        validated_response = validate_and_repair_response(response, subject_chunk)
        
        if not validated_response:
            logger.error(f"Failed to get valid response for {subject}, student {student_id}")
            # Return fallback for each topic
            fallback = []
            for topic in subject_chunk.get("topics", []):
                topic_name = topic.get("topic_name", "Unknown")
                fallback.append({
                    "test_name": subject_chunk.get("test_name", "Unknown"),
                    "subject": subject,
                    "topic_name": topic_name,
                    "topic_metadata": metadata_map.get(topic_name, {}),
                    "strength_insights": ["Insufficient data available."],
                    "weakness_insights": ["Insufficient data available."],
                    "learning_recommendations": ["Insufficient data available."]
                })
            return fallback
        
        # Merge metadata into validated response
        for insight in validated_response:
            topic_name = insight.get("topic_name", "Unknown")
            insight["topic_metadata"] = metadata_map.get(topic_name, {})
        
        logger.info(f"Successfully analyzed {subject} with {len(validated_response)} topics")
        return validated_response
        
    except Exception as e:
        logger.error(f"Error analyzing {subject} for student {student_id}: {e}")
        # Return fallback
        fallback = []
        for topic in subject_chunk.get("topics", []):
            topic_name = topic.get("topic_name", "Unknown")
            fallback.append({
                "test_name": subject_chunk.get("test_name", "Unknown"),
                "subject": subject,
                "topic_name": topic_name,
                "topic_metadata": metadata_map.get(topic_name, {}),
                "strength_insights": ["Analysis failed due to error."],
                "weakness_insights": ["Analysis failed due to error."],
                "learning_recommendations": ["Please review manually."]
            })
        return fallback


def process(student_chunks: Dict[str, List[Dict]], target_class: str = None) -> int:
    """
    Process all students' subject chunks through LLM
    Writes each student's output immediately after completion
    Returns: count of students processed
    """
    setup_gemini()
    
    total_students = len(student_chunks)
    processed_count = 0
    
    logger.info(f"Starting LLM analysis for {total_students} students")
    
    for idx, (student_id, subject_chunks) in enumerate(student_chunks.items(), 1):
        logger.info(f"[{idx}/{total_students}] Processing student {student_id} with {len(subject_chunks)} subjects")
        
        student_insights = []
        
        for subject_chunk in subject_chunks:
            # Analyze this subject
            topic_insights = analyze_subject_chunk(subject_chunk, student_id)
            student_insights.extend(topic_insights)
            
            # Rate limiting
            time.sleep(1)
        
        # Write student file immediately
        write_student_output(student_id, student_insights, target_class)
        processed_count += 1
        
        logger.info(f"Completed student {student_id}: {len(student_insights)} topic insights, file written")
    
    logger.info(f"LLM analysis complete for all {total_students} students")
    return processed_count


if __name__ == "__main__":
    # For testing
    from src.phase2.data_processor import process as process_data
    
    student_chunks = process_data()
    results = process(student_chunks)
    
    # Print sample
    sample_student = list(results.keys())[0]
    print(f"\nSample results for student {sample_student}:")
    print(json.dumps(results[sample_student][:2], indent=2))

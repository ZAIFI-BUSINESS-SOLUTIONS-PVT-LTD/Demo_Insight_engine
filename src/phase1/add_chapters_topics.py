import os
import json
import logging
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.phase1.neet_data import chapter_list

logger = setup_logger(__name__)

CHAPTER_TOPIC_ASSIGNMENT_PROMPT = """
You are an expert NEET exam analyzer. You are provided with:
1. A list of NEET questions with their subjects already assigned
2. The complete chapter and topic structure for that subject

Your task is to carefully analyze each question and assign the most appropriate chapter and topic from the provided structure.

IMPORTANT INSTRUCTIONS:
- These are NEET (National Eligibility cum Entrance Test) questions for medical entrance in India
- Read each question carefully and understand what concept it is testing
- Match the question to the MOST SPECIFIC and RELEVANT chapter and topic from the provided structure
- Return ONLY valid JSON - no explanations, no markdown formatting
- If unsure about a topic, choose the closest match from the provided list
- DO NOT create new chapter or topic names - use ONLY the ones provided in the structure

OUTPUT FORMAT (strict JSON):
{
  "assignments": [
    {
      "question_id": "Q46",
      "question_number": 46,
      "chapter": "exact chapter name from structure",
      "topic": "exact topic name from structure"
    },
    ...
  ]
}

Return valid JSON only. No markdown fences, no extra text.
"""

def chunk_questions(questions, chunk_size=45):
    """Split questions into chunks for batch processing"""
    for i in range(0, len(questions), chunk_size):
        yield questions[i:i + chunk_size]

def assign_chapter_topic_for_subject(subject_name, questions, chapter_data):
    """
    Sends questions of a subject to LLM along with chapter/topic structure
    to get chapter and topic assignments.
    
    Args:
        subject_name: Name of the subject
        questions: List of question dicts for this subject
        chapter_data: List of chapter/topic structure for this subject
    
    Returns:
        Dict mapping question_number -> {chapter, topic}
    """
    logger.info(f"Processing {len(questions)} questions for subject: {subject_name}")
    
    assignments = {}
    
    # Process in chunks to avoid token limits
    # Ensure we are sending only the chapter/topic structure for this subject
    if isinstance(chapter_data, dict):
        # If the caller accidentally passed the full mapping, try to extract the subject key
        if subject_name in chapter_data:
            chapter_data = chapter_data[subject_name]
        else:
            # If structure is unexpected, wrap it to avoid sending unrelated data
            chapter_data = [chapter_data]

    # Final sanity: ensure it's a list of chapters
    if not isinstance(chapter_data, list):
        chapter_data = [chapter_data]

    for chunk_idx, q_chunk in enumerate(chunk_questions(questions, chunk_size=45)):
        logger.info(f"  Processing chunk {chunk_idx + 1} ({len(q_chunk)} questions)")
        
        # Prepare input for LLM
        chunk_data = {
            "subject": subject_name,
            "chapter_topic_structure": chapter_data,
            "questions": [
                {
                    "question_id": q.get("question_id"),
                    "question_number": q.get("question_number"),
                    "question_text": q.get("question_text", ""),
                    "options": q.get("options", [])
                }
                for q in q_chunk
            ]
        }
        
        content = json.dumps(chunk_data, indent=2)
        
        try:
            response = call_gemini_json(CHAPTER_TOPIC_ASSIGNMENT_PROMPT, content)
            
            # Extract assignments
            if isinstance(response, dict) and "assignments" in response:
                for item in response["assignments"]:
                    q_num = item.get("question_number")
                    if q_num:
                        assignments[q_num] = {
                            "chapter": item.get("chapter", "Unknown"),
                            "topic": item.get("topic", "Unknown")
                        }
            elif isinstance(response, list):
                # Handle if LLM returns list directly
                for item in response:
                    q_num = item.get("question_number")
                    if q_num:
                        assignments[q_num] = {
                            "chapter": item.get("chapter", "Unknown"),
                            "topic": item.get("topic", "Unknown")
                        }
            
            logger.info(f"  Assigned chapter/topic to {len(assignments)} questions so far")
            
        except Exception as e:
            logger.error(f"  Failed to get assignments for chunk {chunk_idx + 1}: {e}")
            # Continue with other chunks
            continue
    
    return assignments

def process():
    """
    Main entry point: assigns chapter and topic to each question based on subject
    and NEET chapter/topic structure using LLM analysis.
    """
    setup_gemini()
    
    qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")
    
    if not os.path.exists(qp_path):
        # Fallback: search for any class folder that contains phase1/questionpaper.json
        import glob
        pattern = os.path.join(Config.OUTPUT_DIR, "*", "phase1", "questionpaper.json")
        matches = glob.glob(pattern)
        if matches:
            qp_path = matches[0]
            logger.info(f"Using found question paper JSON at: {qp_path}")
            print(f"Found questionpaper.json at: {qp_path}")
        else:
            raise FileNotFoundError(f"Question paper JSON not found: {qp_path}")
    
    logger.info(f"Reading question paper from {qp_path}")
    
    # Load existing questionpaper.json (should have subjects assigned)
    with open(qp_path, 'r', encoding='utf-8') as f:
        qp_data = json.load(f)
        questions = qp_data.get("questions") if isinstance(qp_data, dict) else qp_data
    
    if not questions:
        logger.warning("No questions found in questionpaper.json")
        return
    
    # Group questions by subject
    questions_by_subject = {}
    for q in questions:
        subject = q.get("subject", "Unknown")
        if subject not in questions_by_subject:
            questions_by_subject[subject] = []
        questions_by_subject[subject].append(q)
    
    logger.info(f"Found {len(questions_by_subject)} subjects to process")
    
    # Process each subject
    all_assignments = {}
    
    for subject_name, subject_questions in questions_by_subject.items():
        if subject_name == "Unknown":
            logger.warning(f"Skipping {len(subject_questions)} questions with 'Unknown' subject")
            continue
        
        # Get chapter/topic structure for this subject
        if subject_name not in chapter_list:
            logger.warning(f"No chapter data found for subject '{subject_name}' in neet_data.py")
            # Assign default values
            for q in subject_questions:
                q_num = q.get("question_number")
                if q_num:
                    all_assignments[q_num] = {
                        "chapter": "Unknown",
                        "topic": "Unknown"
                    }
            continue
        
        chapter_data = chapter_list[subject_name]
        
        # Get assignments from LLM
        subject_assignments = assign_chapter_topic_for_subject(
            subject_name,
            subject_questions,
            chapter_data
        )
        
        all_assignments.update(subject_assignments)
    
    # Update questions with chapter and topic
    updated_count = 0
    for q in questions:
        q_num = q.get("question_number")
        if q_num and q_num in all_assignments:
            q["chapter"] = all_assignments[q_num]["chapter"]
            q["topic"] = all_assignments[q_num]["topic"]
            updated_count += 1
        else:
            # Default values if not assigned
            q["chapter"] = q.get("chapter", "Unknown")
            q["topic"] = q.get("topic", "Unknown")
    
    logger.info(f"Assigned chapter/topic to {updated_count} questions")
    
    # Save updated questionpaper.json
    output_data = {"questions": questions}
    with open(qp_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    logger.info(f"Updated questionpaper.json with chapter and topic assignments")
    
    # Print summary
    print("\nChapter/Topic assignment summary:")
    chapter_counts = {}
    for q in questions:
        subj = q.get("subject", "Unknown")
        chap = q.get("chapter", "Unknown")
        key = f"{subj} - {chap}"
        chapter_counts[key] = chapter_counts.get(key, 0) + 1
    
    for key, count in sorted(chapter_counts.items()):
        print(f"  {key}: {count} questions")

if __name__ == "__main__":
    process()

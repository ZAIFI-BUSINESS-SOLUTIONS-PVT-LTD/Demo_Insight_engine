import sys
import os
import json
import logging
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase2 import data_processor, llm_analyzer, output_writer
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case2Runner")

def verify_student_output(student_id, students_dir):
    """Verify that a student's output file exists and is valid"""
    output_path = os.path.join(students_dir, f"{student_id}.json")
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Student output not found: {output_path}")
    if os.path.getsize(output_path) < 10:
        raise ValueError(f"Student output file too small: {output_path}")
    logger.info(f"Verified student output: {student_id}")

def main():
    try:
        # Prefer explicit environment variable
        env_class = os.getenv("TARGET_CLASS")

        # Discover available classes (those with phase1/merged.json)
        available = []
        if os.path.exists(Config.OUTPUT_DIR):
            for d in os.listdir(Config.OUTPUT_DIR):
                class_path = os.path.join(Config.OUTPUT_DIR, d)
                merged_path = os.path.join(class_path, "phase1", "merged.json")
                if os.path.isdir(class_path) and os.path.exists(merged_path):
                    available.append(d)

        if env_class and env_class.strip().lower() != "none":
            # Use environment override (non-interactive)
            classes_to_process = [env_class]
        else:
            # Interactive prompt: require user to pick from available classes or 'all'
            if not available:
                logger.error("No classes found to process. Ensure phase1/merged.json exists.")
                sys.exit(1)

            prompt_msg = f"Available classes: {', '.join(available)}\nEnter class folder name (or 'all' to process all): "
            try:
                choice = input(prompt_msg).strip()
            except Exception:
                # Non-interactive fallback
                logger.error("No class provided and input() unavailable. Set TARGET_CLASS or run interactively.")
                sys.exit(1)

            if not choice:
                logger.error("No class entered. Aborting.")
                sys.exit(1)

            if choice.lower() == 'all':
                classes_to_process = available
            elif choice in available:
                classes_to_process = [choice]
            else:
                logger.error(f"Invalid class selection: {choice}")
                sys.exit(1)

        logger.info(f"Classes to process: {classes_to_process}")

        for current_class in classes_to_process:
            # Patch Config.DEFAULT_CLASS for this iteration
            Config.DEFAULT_CLASS = current_class
            
            logger.info(f"=== Starting Phase 2 Execution for {current_class} ===")
            
            # Step 1: Process and group data (student → subject → topic)
            logger.info(f"--- Step 1: Data Processing ({current_class}) ---")
            student_chunks = data_processor.process(current_class)
            
            if not student_chunks:
                logger.warning(f"No student data generated for {current_class}. Skipping...")
                continue
            
            logger.info(f"Prepared data for {len(student_chunks)} students")
            
            # Step 2: LLM Analysis (one subject at a time per student)
            # Each student's output is written immediately after their analysis completes
            logger.info(f"--- Step 2: LLM Analysis & Writing Outputs ({current_class}) ---")
            processed_count = llm_analyzer.process(student_chunks, current_class)
            
            if processed_count == 0:
                logger.warning(f"No students processed for {current_class}!")
                continue
            
            logger.info(f"Completed analysis and file writing for {processed_count} students")
            
            # Step 3: Write index file
            logger.info(f"--- Step 3: Write Index File ({current_class}) ---")
            student_ids = list(student_chunks.keys())
            output_writer.write_index_file(student_ids, current_class)
            
            # Step 4: Verification
            logger.info(f"=== Verifying Outputs for {current_class} ===")
            
            students_dir = os.path.join(Config.OUTPUT_DIR, "students")
            index_path = os.path.join(students_dir, "_index.json")
            
            try:
                # Verify index file
                if not os.path.exists(index_path):
                    raise FileNotFoundError(f"Index file not found: {index_path}")
                logger.info(f"Verified index file: {index_path}")
                
                # Verify sample student outputs (first 3)
                sample_students = student_ids[:3]
                for student_id in sample_students:
                    verify_student_output(student_id, students_dir)
                
                logger.info(f"=== SUCCESS: {current_class} Phase 2 Completed and Verified ===")
                logger.info(f"Student outputs written to: {students_dir}")
                
            except Exception as e:
                logger.error(f"Verification Failed for {current_class}: {e}")

    except Exception:
        logger.error("Phase 2 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

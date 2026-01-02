import sys
import os
import logging
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase4 import aggregator
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case4Runner")


def main():
    try:
        logger.info("=== Starting Phase 4 Execution: Multi-Test Student Aggregation ===")
        
        # Step 1: Process aggregation (prompts user for classes)
        logger.info("--- Step 1: Aggregate Student Data Across Classes ---")
        student_data = aggregator.process()
        
        if not student_data:
            logger.error("No student data aggregated. Phase 4 failed.")
            sys.exit(1)
        
        logger.info(f"Aggregated data for {len(student_data)} students")
        
        # Verification
        logger.info("=== Verification ===")
        output_dir = os.path.join(Config.OUTPUT_DIR, "phase4", "students")
        index_path = os.path.join(output_dir, "_index.json")
        
        if os.path.exists(index_path):
            logger.info(f"✓ Verified index file: {index_path}")
        else:
            logger.error(f"✗ Index file not found: {index_path}")
        
        # Verify sample student files
        sample_count = min(3, len(student_data))
        for student_id in list(student_data.keys())[:sample_count]:
            student_path = os.path.join(output_dir, f"{student_id}.json")
            if os.path.exists(student_path):
                logger.info(f"✓ Verified student file: {student_id}.json")
            else:
                logger.error(f"✗ Student file not found: {student_id}.json")
        
        logger.info("=== SUCCESS: Phase 4 Completed ===")
        logger.info(f"Student files written to: {output_dir}")
        
    except Exception:
        logger.error("Phase 4 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

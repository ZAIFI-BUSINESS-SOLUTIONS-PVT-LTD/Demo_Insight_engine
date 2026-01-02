import sys
import os
import logging
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase5 import data_processor, llm_analyzer, output_writer
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case5Runner")


def main():
    try:
        logger.info("=== Starting Phase 5 Execution: Cross-Test Pattern Analysis ===")
        
        # Step 1: Process student data (filter wrong questions, group by topic)
        logger.info("--- Step 1: Data Processing (Wrong Questions Analysis) ---")
        student_data = data_processor.process()
        
        if not student_data:
            logger.error("No student data with weak topics found. Phase 5 cannot proceed.")
            sys.exit(1)
        
        logger.info(f"Processed {len(student_data)} students with weak topics")
        
        # Step 2: LLM Analysis (1 call per student: unified insights)
        logger.info("--- Step 2: LLM Analysis (Pattern Recognition) ---")
        all_insights = llm_analyzer.process(student_data)
        
        if not all_insights:
            logger.error("No insights generated. Phase 5 failed.")
            sys.exit(1)
        
        logger.info(f"Generated insights for {len(all_insights)} students")
        
        # Step 3: Write outputs
        logger.info("--- Step 3: Write Outputs ---")
        output_writer.process(all_insights)
        
        # Verification
        logger.info("=== Verification ===")
        output_dir = os.path.join(Config.OUTPUT_DIR, "phase5")
        insights_json = os.path.join(output_dir, "student_pattern_insights.json")
        
        if os.path.exists(insights_json):
            logger.info(f"✓ Verified insights JSON: {insights_json}")
        else:
            logger.error(f"✗ Insights JSON not found: {insights_json}")
        
        logger.info("=== SUCCESS: Phase 5 Completed ===")
        logger.info(f"Pattern insights written for {len(all_insights)} students")
        
    except Exception:
        logger.error("Phase 5 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

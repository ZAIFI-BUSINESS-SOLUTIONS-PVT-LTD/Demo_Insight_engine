import sys
import os
import logging
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase3 import data_aggregator, llm_analyzer, output_writer
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case3Runner")


def main():
    try:
        logger.info("=== Starting Phase 3 Execution: Pattern Analysis ===")
        
        # Step 1: Aggregate student data (group by topic across tests)
        logger.info("--- Step 1: Data Aggregation ---")
        student_data = data_aggregator.process()
        
        if not student_data:
            logger.error("No student data loaded. Phase 3 cannot proceed.")
            sys.exit(1)
        
        logger.info(f"Loaded {len(student_data)} students for pattern analysis")
        
        # Step 2: LLM Analysis (one call per student)
        logger.info("--- Step 2: Pattern Analysis (LLM) ---")
        all_insights = llm_analyzer.process(student_data)
        
        if not all_insights:
            logger.error("No insights generated. Phase 3 failed.")
            sys.exit(1)
        
        logger.info(f"Generated insights for {len(all_insights)} students")
        
        # Step 3: Write outputs
        logger.info("--- Step 3: Write Outputs ---")
        output_writer.process(all_insights)
        
        # Verification
        logger.info("=== Verification ===")
        output_dir = os.path.join(Config.OUTPUT_DIR, "phase3")
        csv_path = os.path.join(output_dir, "student_pattern_insights.csv")
        
        if os.path.exists(csv_path):
            logger.info(f"✓ Verified CSV output: {csv_path}")
        else:
            logger.error(f"✗ CSV output not found: {csv_path}")
        
        logger.info("=== SUCCESS: Phase 3 Completed ===")
        logger.info(f"Pattern insights written for {len(all_insights)} students")
        
    except Exception:
        logger.error("Phase 3 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

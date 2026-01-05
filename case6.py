"""
Phase 6 Entry Point: PDF Report Generation
Generates per-student PDF reports combining:
- Test-wise subject-wise performance charts (from phase4)
- Pattern insights (from phase5)
"""
import os
import sys
from dotenv import load_dotenv
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


def main():
    """
    Main entry point for Phase 6 PDF report generation
    """
    logger.info("=" * 80)
    logger.info("PHASE 6: PDF REPORT GENERATION")
    logger.info("=" * 80)
    
    # Get target student from environment (optional)
    target_student = os.getenv("STUDENT_NAME", "").strip()
    
    if target_student:
        logger.info(f"Target student: {target_student}")
    else:
        logger.info("Target: ALL students")
    
    try:
        # Import phase6 module
        from src.phase6.generate_reports import process
        
        # Generate reports
        report_count = process(target_student_id=target_student if target_student else None)
        
        logger.info("=" * 80)
        logger.info(f"PHASE 6 COMPLETE: {report_count} reports generated")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Phase 6 failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

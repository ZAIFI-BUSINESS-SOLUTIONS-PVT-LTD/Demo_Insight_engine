"""
Test script for Phase 6 PDF generation
Generates a report for a single student to validate the implementation
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.phase6.generate_reports import process
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_single_student():
    """Test PDF generation for a single student"""
    test_student_id = "2025300001"
    
    logger.info("=" * 80)
    logger.info(f"TESTING PHASE 6: Generating report for student {test_student_id}")
    logger.info("=" * 80)
    
    try:
        report_count = process(target_student_id=test_student_id)
        
        if report_count > 0:
            logger.info(f"✅ SUCCESS: Generated {report_count} report(s)")
            logger.info(f"Check output/phase6/reports/{test_student_id}_report.pdf")
            return True
        else:
            logger.error(f"❌ FAILED: No reports generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def test_all_students():
    """Test PDF generation for all students"""
    logger.info("=" * 80)
    logger.info("TESTING PHASE 6: Generating reports for ALL students")
    logger.info("=" * 80)
    
    try:
        report_count = process(target_student_id=None)
        
        logger.info(f"✅ COMPLETE: Generated {report_count} report(s)")
        logger.info("Check output/phase6/reports/ directory")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PHASE 6 TEST SCRIPT")
    print("=" * 80)
    print("\nOptions:")
    print("  1. Test single student (2025300001)")
    print("  2. Test all students")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        success = test_single_student()
    elif choice == "2":
        success = test_all_students()
    else:
        print("Exiting...")
        sys.exit(0)
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed. Check logs for details.")
        sys.exit(1)

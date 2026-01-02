import sys
import os
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase0.runner import Phase0Runner
from src.utils.logger import setup_logger

logger = setup_logger("Case0Runner")

def main():
    try:
        runner = Phase0Runner()
        runner.run()
    except Exception:
        logger.error("Phase 0 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

import os
import sys
import subprocess
import logging

# Setup simple logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PipelineRunner")

def run_step(script_name):
    logger.info(f"========== Running {script_name} ==========")
    try:
        # Run the script using the current python executable
        result = subprocess.run([sys.executable, script_name], check=True)
        logger.info(f"========== {script_name} Completed Successfully ==========\n")
    except subprocess.CalledProcessError as e:
        logger.error(f"========== {script_name} FAILED ==========")
        sys.exit(1)

def main():
    # 1. Determine Target Class
    target_class = None
    
    # Check CLI args first
    if len(sys.argv) > 1:
        target_class = sys.argv[1]
    
    # Update Env Var if provided
    if target_class:
        logger.info(f"Setting TARGET_CLASS = {target_class}")
        os.environ["TARGET_CLASS"] = target_class
    else:
        current_env = os.getenv("TARGET_CLASS")
        if current_env:
            logger.info(f"Using existing TARGET_CLASS = {current_env}")
        else:
            logger.info("No TARGET_CLASS set. Will run for ALL discovered classes.")

    # 2. Define Pipeline Steps (Phase 0 removed - input CSVs provided directly)
    steps = [
        "case1.py",
        "case2.py",
        "case3.py"
    ]
    
    # 3. Execute Sequence
    for step in steps:
        if not os.path.exists(step):
            logger.error(f"Script file not found: {step}")
            sys.exit(1)
            
        run_step(step)

    logger.info(">>> FULL PIPELINE EXECUTION COMPLETED SUCCESSFULLY <<<")

if __name__ == "__main__":
    main()

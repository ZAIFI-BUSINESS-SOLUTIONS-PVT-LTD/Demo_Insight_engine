
import sys
import os

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase3 import pipeline

if __name__ == "__main__":
    pipeline.run()

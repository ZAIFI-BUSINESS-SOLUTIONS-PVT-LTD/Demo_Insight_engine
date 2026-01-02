"""
Test script to validate merge_data.py works with CSV inputs
This simulates having questionpaper.json already created
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase1 import merge_data
from src.config import Config

# Set test class
Config.DEFAULT_CLASS = "class_7"

# Create a dummy questionpaper.json for testing (simulating LLM extraction result)
output_dir = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1")
os.makedirs(output_dir, exist_ok=True)

# Create minimal questionpaper.json with first 5 questions
dummy_questions = {
    "questions": [
        {
            "question_number": i,
            "question_id": f"Q{i}",
            "question_text": f"Sample question {i} text",
            "options": [f"(A) Option A for Q{i}", f"(B) Option B for Q{i}", 
                       f"(C) Option C for Q{i}", f"(D) Option D for Q{i}"]
        }
        for i in range(1, 6)
    ]
}

qp_path = os.path.join(output_dir, "questionpaper.json")
with open(qp_path, 'w', encoding='utf-8') as f:
    json.dump(dummy_questions, f, indent=2)

print(f"Created dummy questionpaper.json at: {qp_path}")
print("Now running merge_data.process()...\n")

# Run merge
try:
    merge_data.process()
    print("\n✓ Merge completed successfully!")
    
    # Show sample of merged output
    merged_path = os.path.join(output_dir, "merged.json")
    with open(merged_path, 'r', encoding='utf-8') as f:
        merged = json.load(f)
    
    print(f"\nCreated {len(merged)} records")
    print(f"\nFirst 2 records:")
    print(json.dumps(merged[:2], indent=2))
    
except Exception as e:
    print(f"\n✗ Merge failed: {e}")
    import traceback
    traceback.print_exc()

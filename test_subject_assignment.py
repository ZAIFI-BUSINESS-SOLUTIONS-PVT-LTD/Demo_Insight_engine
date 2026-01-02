"""
Test script to demonstrate subject assignment flow
This shows how the interactive prompt works and validates the output
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase1 import add_subjects
from src.config import Config

# Set test class
Config.DEFAULT_CLASS = "class_7"

print("""
=================================================================
SUBJECT ASSIGNMENT TEST
=================================================================

This script demonstrates the interactive subject assignment feature.

After extracting questions from the PDF, you will be prompted to:
1. Enter subject names and their question ranges
2. The system will automatically add a 'subject' field to each question

Example input format:
  Physics 1 45
  Chemistry 46 90
  Botany 91 135
  Zoology 136 180
  done

The questionpaper.json will be updated with subject fields.
=================================================================
""")

# Check if questionpaper.json exists
qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")

if not os.path.exists(qp_path):
    print(f"ERROR: Question paper JSON not found at: {qp_path}")
    print("Please run case1.py first to extract questions from the PDF.")
    sys.exit(1)

print(f"Found questionpaper.json at: {qp_path}")

# Show current questions (first 3 and last 3)
with open(qp_path, 'r', encoding='utf-8') as f:
    qp_data = json.load(f)
    questions = qp_data.get("questions", [])

print(f"\nCurrent question count: {len(questions)}")
if questions:
    print(f"Question number range: Q{questions[0].get('question_number')} to Q{questions[-1].get('question_number')}")
    print(f"\nFirst question: {questions[0].get('question_number')} - {questions[0].get('question_text', '')[:60]}...")
    print(f"Last question: {questions[-1].get('question_number')} - {questions[-1].get('question_text', '')[:60]}...")

print("\n" + "="*60)
print("Starting interactive subject assignment...")
print("="*60 + "\n")

# Run the subject assignment
try:
    add_subjects.process()
    
    print("\n" + "="*60)
    print("✓ Subject assignment completed!")
    print("="*60)
    
    # Show sample of updated data
    with open(qp_path, 'r', encoding='utf-8') as f:
        updated_data = json.load(f)
        updated_questions = updated_data.get("questions", [])
    
    print(f"\nSample of updated questions (showing first 3):")
    for i, q in enumerate(updated_questions[:3]):
        print(f"\nQuestion {q.get('question_number')}:")
        print(f"  Subject: {q.get('subject', 'Unknown')}")
        print(f"  Text: {q.get('question_text', '')[:80]}...")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

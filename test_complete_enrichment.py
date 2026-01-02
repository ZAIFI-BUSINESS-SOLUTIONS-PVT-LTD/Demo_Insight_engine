"""
Test script to demonstrate the complete enrichment pipeline:
Subject -> Chapter -> Topic assignment

This shows the full flow after question extraction.
"""
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config

# Set test class
Config.DEFAULT_CLASS = "class_7"

print("""
=================================================================
COMPLETE ENRICHMENT PIPELINE TEST
=================================================================

This demonstrates the full enrichment flow for NEET questions:

Pipeline Steps:
1. Extract Question Paper (LLM extracts questions from PDF)
2. Assign Subjects (Interactive: user defines subject ranges)
3. Assign Chapters & Topics (LLM analyzes each question)
4. Create Merged JSON (combines with answer key & responses)

After running case1.py, your questionpaper.json will include:
- question_number, question_id, question_text, options (from extraction)
- subject (from interactive assignment)
- chapter, topic (from LLM analysis using neet_data.py)

And merged.json will include all fields for each (student, question) pair.
=================================================================
""")

# Check if questionpaper.json exists
qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")

if os.path.exists(qp_path):
    print(f"\n✓ Found questionpaper.json at: {qp_path}")
    
    with open(qp_path, 'r', encoding='utf-8') as f:
        qp_data = json.load(f)
        questions = qp_data.get("questions", [])
    
    print(f"\nQuestion count: {len(questions)}")
    
    if questions:
        # Show sample question with all enrichments
        print(f"\nSample question (first one):")
        sample = questions[0]
        print(json.dumps(sample, indent=2))
        
        # Count enrichments
        has_subject = sum(1 for q in questions if q.get("subject") and q.get("subject") != "Unknown")
        has_chapter = sum(1 for q in questions if q.get("chapter") and q.get("chapter") != "Unknown")
        has_topic = sum(1 for q in questions if q.get("topic") and q.get("topic") != "Unknown")
        
        print(f"\nEnrichment status:")
        print(f"  Questions with subject: {has_subject}/{len(questions)}")
        print(f"  Questions with chapter: {has_chapter}/{len(questions)}")
        print(f"  Questions with topic: {has_topic}/{len(questions)}")
else:
    print(f"\n✗ Question paper JSON not found at: {qp_path}")
    print("\nTo run the complete pipeline:")
    print("  python case1.py")

# Check merged.json
merged_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "merged.json")

if os.path.exists(merged_path):
    print(f"\n✓ Found merged.json at: {merged_path}")
    
    with open(merged_path, 'r', encoding='utf-8') as f:
        merged = json.load(f)
    
    print(f"\nMerged records count: {len(merged)}")
    
    if merged:
        print(f"\nSample merged record (first one):")
        print(json.dumps(merged[0], indent=2))
        
        # Check field completeness
        has_all_fields = sum(1 for r in merged if all(
            k in r for k in ["subject", "chapter", "topic", "correct_option", "student_selected_option"]
        ))
        print(f"\nRecords with complete enrichment: {has_all_fields}/{len(merged)}")
else:
    print(f"\n✗ Merged JSON not found at: {merged_path}")

print("\n" + "="*65)
print("RUNNING THE PIPELINE")
print("="*65)
print("""
To execute the complete pipeline with all enrichments:

  python case1.py

You will be prompted to enter subject ranges, then:
- LLM will extract questions from PDF
- You assign subjects interactively
- LLM assigns chapters and topics automatically
- Merge creates final student-question records

The pipeline handles:
- Flexible PDF naming (question_paper.pdf, QuestionPaper.pdf)
- Multi-word subject names
- Batch processing for LLM (15 questions per chunk)
- Graceful handling of missing data
""")

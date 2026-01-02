phase1.md
 
Pace Academy — Phase 1: Data Ingestion & Normalization
 
 
---
 
1. Phase 1 Objective (Very Strict)
 
Phase 1 exists to convert raw exam inputs into clean, structured, merge-ready data.
 
Inputs
 
QuestionPaper.pdf
 
Solutions.pdf
 
ResponseSheet.csv
 
 
Outputs
 
JSON (ground truth)
 
CSV (mechanical analytics)
 
 
Phase 1 does NOT:
 
Generate insights
 
Use reasoning LLMs for evaluation
 
Interpret student behavior
 
Personalize feedback
 
 
This phase protects data integrity only.
 
 
---
 
2. Folder Scope (As Enforced)
 
Inputs
 
input/
└── class_10/
    ├── QuestionPaper.pdf
    ├── Solutions.pdf
    └── ResponseSheet.csv
 
Outputs
 
output/
└── class_10/
    └── phase1/
        ├── questionpaper.json
        ├── solution.json
        ├── merged.json
        ├── student_question_analysis.csv
        ├── student_summary.csv
        └── question_summary.csv
 
Class name must be config-driven, not hardcoded.
 
 
---
 
3. Phase 1 High-Level Flow
 
QuestionPaper.pdf ──▶ LLM ──▶ questionpaper.json
Solutions.pdf     ──▶ LLM ──▶ solution.json
                           ↓
                    Merge + Validate
                           ↓
                      merged.json
                           ↓
            Mechanical Student Analytics (CSV)
 
 
---
 
4. LLM Usage (Controlled)
 
Model
 
Gemini 3.0 Flash
 
 
Allowed Usage
 
Extract structured content from PDFs
 
Convert images to English descriptions
 
 
Not Allowed
 
Inferring answers in question paper
 
Changing solution correctness
 
Reinterpreting question intent
 
 
LLM is a parser, not a thinker.
 
 
---
 
5. Question Paper Extraction
 
Input
 
input/class_10/QuestionPaper.pdf
 
 
Output
 
output/class_10/phase1/questionpaper.json
 
 
JSON Contract (Non-Negotiable)
 
{
  "exam": "PACE_CLASS_10",
  "questions": [
    {
      "question_id": "Q1",
      "question_number": 1,
      "question_text": "string",
      "question_image_description": "string | null",
      "options": {
        "A": {
          "text": "string",
          "image_description": "string | null"
        },
        "B": {
          "text": "string",
          "image_description": "string | null"
        },
        "C": {
          "text": "string",
          "image_description": "string | null"
        },
        "D": {
          "text": "string",
          "image_description": "string | null"
        }
      }
    }
  ]
}
 
Rules
 
question_id = "Q" + question_number
 
No base64
 
No markdown
 
Missing data → null
 
Never infer correct option here
 
 
 
---
 
6. Solution Extraction
 
Input
 
input/class_10/Solutions.pdf
 
 
Output
 
output/class_10/phase1/solution.json
 
 
JSON Contract
 
{
  "solutions": [
    {
      "question_id": "Q1",
      "correct_option": "A",
      "solution_text": "string",
      "solution_image_description": "string | null",
      "key_concept": "string"
    }
  ]
}
 
Rules
 
Must map to existing question_id
 
If unclear → "correct_option": "UNKNOWN"
 
No reasoning beyond what is written
 
 
 
---
 
7. Merge Logic
 
Inputs
 
questionpaper.json
 
solution.json
 
 
Output
 
merged.json
 
 
Merge Rules
 
Join strictly on question_id
 
Preserve original question order
 
Do not drop unmatched entries
 
 
merged.json Contract
 
{
  "question_id": "Q1",
  "question_number": 1,
  "question_text": "string",
  "options": { "A": {}, "B": {}, "C": {}, "D": {} },
  "correct_option": "A",
  "solution_text": "string",
  "key_concept": "Motion"
}
 
 
---
 
8. Response Sheet Consumption
 
Input
 
input/class_10/ResponseSheet.csv
 
 
Required Columns
 
student_id
 
question_id (or question_number → must be converted)
 
selected_option
 
marks_obtained
 
attempted (Y/N)
 
 
If this schema breaks → stop Phase 1.
 
 
---
 
9. Mechanical Student Analytics (NO LLM)
 
Join
 
merged.json × ResponseSheet.csv
 
 
Derived Fields
 
is_attempted
 
is_correct
 
marks_lost
 
wrong_option_selected
 
 
No interpretation.
 
 
---
 
10. Phase 1 CSV Outputs
 
10.1 student_question_analysis.csv
 
(1 row = student × question)
 
Columns:
 
student_id
 
question_id
 
selected_option
 
correct_option
 
is_correct
 
attempted
 
marks_obtained
 
marks_lost
 
key_concept
 
 
 
---
 
10.2 student_summary.csv
 
(1 row = student)
 
Columns:
 
student_id
 
total_marks
 
accuracy_percentage
 
attempt_percentage
 
strongest_concept
 
weakest_concept
 
 
Computed statistically only
(no LLM, no language generation)
 
 
---
 
10.3 question_summary.csv
 
(1 row = question)
 
Columns:
 
question_id
 
attempt_percentage
 
correct_percentage
 
most_common_wrong_option
 
difficulty_tag
 
 
Difficulty logic:
 
> 70% correct → Easy
 
 
 
40–70% → Medium
 
<40% → Hard
 
 
 
---
 
11. Validation Rules
 
Phase 1 must fail fast if:
 
Duplicate question_id detected
 
Invalid options (not A/B/C/D)
 
Missing solution for a question
 
Question count mismatch
 
 
All failures must be logged.
 
 
---
 
12. Phase Boundary (Critical)
 
Phase 1 ENDS HERE.
 
Outputs from Phase 1 are:
 
Inputs to Phase 2
 
Treated as ground truth
 
Never modified by Phase 2 logic
 
 
 
---
 
13. Phase 1 Success Criteria
 
Phase 1 is complete when:
 
All JSONs validate against schema
 
All CSVs are generated
 
Phase 2 can consume outputs without schema changes
 
 
 
---
 
14. Final Note
 
If Phase 1 is clean,
Phase 2 becomes trivial.
 
This file exists to remove ambiguity
 
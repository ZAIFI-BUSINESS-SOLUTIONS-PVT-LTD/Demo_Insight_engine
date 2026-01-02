 
phase2.md
 
---
 
1. Phase 2 Objective (Strict)
 
Phase 2 exists to add reasoning on top of Phase 1 ground truth.
 
It converts:
 
Structured exam truth (merged.json)
 
Student responses (ResponseSheet.csv)
 
 
into:
 
Student-level qualitative insights (CSV)
 
 
Phase 2 does NOT:
 
Modify correctness
 
Re-score marks
 
Reinterpret questions
 
Generate predictions or prescriptions
 
 
Phase 2 is reasoning only, grounded on Phase 1 data.
 
 
---
 
2. Folder Scope (As Enforced)
 
Inputs (Read-Only)
 
output/
└── class_10/
    └── phase1/
        ├── merged.json
        ├── student_question_analysis.csv
 
Outputs
 
output/
└── class_10/
    └── phase2/
        ├── student_question_insights.csv
        └── student_insight_summary.csv
 
Phase 2 must never write into phase1/.
 
 
---
 
3. Phase 2 High-Level Flow
 
merged.json
      +
student_question_analysis.csv
      ↓
Student-wise Question Packets
      ↓
LLM Reasoning (per student)
      ↓
Phase 2 CSV Outputs
 
 
---
 
4. Ground Truth Contract (Non-Negotiable)
 
The following fields are final and immutable:
 
question_id
 
question_text
 
options
 
correct_option
 
selected_option
 
marks_obtained
 
key_concept
 
difficulty_tag
 
 
LLM must accept these as facts.
 
 
---
 
5. Packetization Logic (No LLM)
 
For each student_id:
 
Create a Student Question Packet containing:
 
question_id
 
question_text
 
options (A/B/C/D)
 
correct_option
 
student_selected_option
 
is_correct
 
key_concept
 
difficulty_tag
 
solution_text
 
 
This step is purely mechanical.
 
 
---
 
6. LLM Usage (Controlled & Scoped)
 
Model
 
Gemini 3.0 Flash
 
 
Call Strategy
 
One student per LLM call
 
Low temperature
 
Deterministic output format
 
 
LLM Is Allowed To
 
Explain why an answer is right or wrong
 
Identify concept-level misunderstanding
 
Detect patterns across questions
 
 
LLM Is NOT Allowed To
 
Change correct_option
 
Invent new concepts
 
Assign marks
 
Suggest study plans
 
 
LLM is a reasoning layer, not an authority.
 
 
---
 
7. LLM Output Responsibilities
 
For each question:
 
correctness_reason (max 2 lines)
 
mistake_type
 
Conceptual
 
Calculation
 
Guess
 
Careless
 
 
confidence_signal
 
Low / Medium / High
 
 
 
For each student (aggregated):
 
strongest_concepts (max 3)
 
weakest_concepts (max 3)
 
dominant_mistake_pattern
 
overall_summary (max 3 lines)
 
 
 
---
 
8. Phase 2 CSV Outputs
 
8.1 student_question_insights.csv
 
(1 row = student × question)
 
Columns:
 
student_id
 
question_id
 
selected_option
 
correct_option
 
is_correct
 
mistake_type
 
correctness_reason
 
confidence_signal
 
key_concept
 
difficulty_tag
 
 
 
---
 
8.2 student_insight_summary.csv
 
(1 row = student)
 
Columns:
 
student_id
 
accuracy_percentage
 
attempt_percentage
 
strongest_concepts
 
weakest_concepts
 
dominant_mistake_pattern
 
llm_summary
 
 
 
---
 
9. Execution Rules
 
Phase 2 never retries reasoning calls
 
If LLM output is malformed → flag student
 
Partial student insights are acceptable
 
CSV is the only final output format
 
 
 
---
 
10. Validation Rules
 
Phase 2 must fail or flag if:
 
question_id mismatch with Phase 1
 
selected_option not in A/B/C/D
 
correct_option missing
 
LLM output violates schema
 
 
 
---
 
11. Phase Boundary (Critical)
 
Phase 2 is terminal for this project.
 
Its outputs may be:
 
Shown to clients
 
Consumed by UI later
 
Used for demos
 
 
But no further mutation happens here.
 
 
---
 
12. Success Criteria
 
Phase 2 is successful if:
 
Every student has reasoning-level output
 
No Phase 1 data is altered
 
CSVs are clean, readable, and consistent
 
 
 
---
 
13. Final Note
 
Phase 1 protects truth.
Phase 2 adds meaning.
 
This file exists so the system does only that — nothing more.

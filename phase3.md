
phase3.md

---

1. Phase 3 Objective (Very Strict)

Phase 3 exists to:
- Read student_insight_summary.csv (Phase 2 output)
- Aggregate student-level insights into class-level teaching intelligence
- Produce teacher-usable guidance, not analytics

Phase 3 produces:
- Focus Zones (what the class collectively struggles with)
- Action Plans (what teachers should do differently)

---

2. Folder Scope (As Enforced)

Inputs (Read-Only):
output/<class_id>/phase2/student_insight_summary.csv

Outputs:
output/class_level_focus_and_action.csv

Phase 3 must not modify, reinterpret, or recompute anything from earlier phases.
Phase 3 writes only its own CSV.

---

3. Processing Logic (Mandatory)

- One Gemini Call Per Class
- Never batch multiple classes
- One class = one LLM call

---

4. Gemini Responsibilities

Gemini must:
- Identify patterns recurring across many students
- Ignore rare or one-off issues
- Focus on conceptual gaps, repeated mistake patterns
- Treat insights as signals, not absolute truth

Gemini must NOT:
- Talk about individual students
- Introduce new syllabus topics
- Re-score or reinterpret correctness
- Use vague language like "some students"

---

5. Output Structure

For each class, extract EXACTLY:
- 3 Focus Zones
- 3 Action Plans

Definitions:
- Focus Zone: A class-level learning gap or behavioral pattern.
- Action Plan: A teacher-level instructional response (HOW to teach differently).

---

6. Final Artifact

File: output/class_level_focus_and_action.csv
Schema:
- class_id
- focus_zone_1
- focus_zone_2
- focus_zone_3
- action_plan_1
- action_plan_2
- action_plan_3

---

7. Success Criteria

Phase 3 is successful when:
- Each class has exactly 3 Focus Zones and 3 Action Plans
- Output is teacher-readable and instructional
- No hallucination, no vagueness, no scope creep
- No earlier phase data is modified

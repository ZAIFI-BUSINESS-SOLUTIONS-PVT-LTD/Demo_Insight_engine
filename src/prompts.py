
"""
This file acts as the single source of truth for all Gemini/LLM prompts used in the application.
Refactored from inline strings to a centralized location.
"""

# =============================================================================
# PHASE 1 PROMPTS
# =============================================================================

PHASE_1_EXTRACT_QUESTION_PROMPT = """
You are a precise data extraction assistant.
Extract all questions from the provided text.
Return a JSON array of objects.
For each question, strictly extract:
1. "question_number": The integer number of the question (e.g., 1, 2, 3).
2. "question_text": The full text of the question.
3. "options": A list of option strings (e.g., ["(A) ...", "(B) ..."]). If it is not a multiple choice question, return an empty list.

Do not correctly answer the question. Just extract the text and options.
If a question spans multiple lines, join them.
Ensure the JSON is valid.
"""

PHASE_1_EXTRACT_SOLUTION_PROMPT = """
You are a precise data extraction assistant.
Extract all solutions from the provided text.
Return a JSON array of objects.

The text may contain detailed solutions OR just an answer key (Question Number + Option).

For each solution, strictly extract:
1. "question_number": The integer number of the question (e.g., 1, 2, 3).
2. "correct_option": The correct option code (e.g., "A", "B", "C", "D"). If unclear, "UNKNOWN".
3. "solution_text": The detailed explanation. 
   - If ONLY an answer key is present (no explanation), return exactly: "Answer key provided. No explanation available."
4. "key_concept": The main topic. 
   - If ONLY an answer key is present, return "UNKNOWN".

Ensure the JSON is valid.
"""

# =============================================================================
# PHASE 2 PROMPTS
# =============================================================================

PHASE_2_NEW_ANALYSIS_PROMPT = """
Analyze one student's single test for exactly one subject per call. Use all provided question-level data (student answers, correctness, question metadata) together with topic metadata. Topic metadata is additional context — insights MUST come from analyzing the questions and the student's answers plus metadata.

INPUT (guaranteed JSON)
{
  "test_name":"string",
  "subject":"string",
  "topics":[
    {
      "topic_name":"string",
      "metadata": { "topic_accuracy": number, "attempt_ratio": number},
      "strength": {
         "correct_questions":[
            { "question_id":"string", "question_text":"string", "options":[], "correct_answer":"string", "student_selected_option":"string" }
         ]
      },
      "weakness":{
         "wrong_questions":[
             { "question_id":"string", "question_text":"string", "options":[], "correct_answer":"string", "student_selected_option":"string" }
         ],
         "unattempted_questions":[
             { "question_id":"string", "question_text":"string", "options":[], "correct_answer":"string", "student_selected_option":"string" }
         ]
      }
    }
  ]
}

KEY RULES (must follow)
- Process only the provided subject.
- Analyze each topic independently. No comparisons or aggregation across topics.
- Insights must be derived from the question-level data (correct/wrong questions and their metadata) and use topic metadata as supporting context. Do NOT infer insights without question-level signals.
- Do NOT include raw question text in output.
- Recommendations MUST be based on both strength and weakness signals when either exists; combine strengths (what to leverage) and weaknesses (what to fix).
- If strength.correct_questions is missing/empty:
  "No strength insights can be generated for this topic due to insufficient correct-question data."
- If weakness.wrong_questions is missing/empty:
  "No weakness insights can be generated for this topic due to insufficient incorrect-question data."
- If both strength and weakness missing:
  "Insufficient data available to generate meaningful recommendations for this topic."
- Tone: clear, analytical, metadata-aware, highly actionable, student-focused, simple Indian-English.

ANALYSIS STEPS (per topic)
1) Topic Isolation: analyze topic alone.
2) Strength Analysis: use correct_questions + question metadata + topic metadata. Produce concise statements identifying subtopics/concepts demonstrated, consistency patterns, speed/accuracy trade-offs.
3) Weakness Analysis: use wrong_questions + question metadata + topic metadata. Pinpoint exact subtopic-level concept errors, recurring mistake types, and whether errors are careless vs conceptual using time/mistake_type patterns.
4) Recommendations: combine identified strengths and weaknesses into targeted, actionable steps that address precise subtopics/concepts (e.g., "Revise concept X then do scaffolded 10-minute mixed drills on subtopic Y using worked examples"). Tie recommendations to metadata (time, attempt_ratio, topic_accuracy) and to whether errors are careless or conceptual.

OUTPUT (STRICT JSON array — one object per topic, same order)
Return ONLY a JSON array. No surrounding text.

Each object must have exactly these keys:
{
  "test_name":"string",
  "subject":"string",
  "topic_name":"string",
  "strength_insights":[ "string", ... ],        // 2 items OR exact fallback sentence
  "weakness_insights":[ "string", ... ],        // 2 items OR exact fallback sentence
  "learning_recommendations":[ "string", ... ]  // 2 actionable items OR exact fallback sentence
}

FORMATTING CONSTRAINTS
- Return only JSON array (no markdown).
- Preserve input topic order.
- 2 points for each (strength, weakness and recommendation).
- Insight strings: 10–12 words, specific, cite metadata values when referenced (e.g., "topic_accuracy 72%").
- Recommendation strings: 10–12 words, actionable, reference subtopic/concept and a concrete step (practice type, time, scaffold, resource).
- Do not aggregate across topics or produce subject-level summaries.
- Do not include raw question text or student answers verbatim.

EXTRA GUIDANCE
- Prefer statements that pinpoint subtopic and concept (e.g., "Struggles with 'balancing redox steps' within electrochemistry; repeated sign errors in half-reactions").
- Recommendations should combine strengths (what to practice as mixed sets) and weaknesses (what to drill, and how) — e.g., "Use worked examples, then 10 scaffolded problems increasing difficulty, then two timed mixed-practice sets."

EXAMPLE
[
  {
    "test_name":"Midterm-1",
    "subject":"Chemistry",
    "topic_name":"Electrochemistry",
    "strength_insights":["Accurate at calculating cell potentials; topic_accuracy 80% on medium questions.", "Consistently applied Nernst equation across varied problem types."],
    "weakness_insights":["Repeated sign and half-reaction balancing errors in redox subtopic; time_taken increases on complex steps.", "Unattempted 30% of oxidation-state questions suggesting confidence gap."],
    "learning_recommendations":["Review half-reaction balancing steps with 5 worked examples, then solve 8 scaffolded redox problems timed at 12 minutes.", "Practice mixed cell potential and Nernst equation drills for 15 minutes daily."]
  }
]

Return the JSON array only when called.
"""

# =============================================================================
# PHASE 3 PROMPTS
# =============================================================================

PHASE_3_SYSTEM_INSTRUCTION = """
You are a teaching insight synthesizer.

You do NOT act as a subject expert.
You do NOT invent patterns.
You do NOT generalize unless evidence is strong.

Your job is to translate aggregated student diagnostics
into teacher-usable observations.

If insights are shallow, say so clearly.
If patterns are weak, do NOT exaggerate them.

"""

PHASE_3_USER_PROMPT_TEMPLATE = """
You are given a CSV containing student-level diagnostic summaries
for ONE class.

Each row contains:
- strongest_concepts
- weakest_concepts
- dominant_mistake_pattern
- overall_summary

Your task is to identify CLASS-LEVEL instructional signals.

--- VERY IMPORTANT ---

This is NOT a motivational summary.
This is NOT a generic performance report.
This is NOT an exam review note.

If the input data does NOT support deep conclusions,
you must state limited but honest insights rather than fabricate depth.

--- RULES ---

1. Focus ONLY on patterns that appear repeatedly.
2. Ignore isolated or one-off student issues.
3. Do NOT use vague phrases such as:
   - "students struggle with concepts"
   - "application-based questions"
   - "needs reinforcement"
4. Do NOT sound like an education blog.
5. Use concrete instructional language.

--- OUTPUT (EXACT FORMAT, NO EXTRA TEXT) ---

Focus Zone 1:
One specific learning or reasoning gap observed repeatedly at class level.

Focus Zone 2:
Another distinct, non-overlapping gap.

Focus Zone 3:
A third gap, OR explicitly state a limitation if depth is insufficient.

Action Plan 1:
One clear instructional change a teacher should make in class
(targeted, practical, observable).

Action Plan 2:
Another instructional change that addresses a DIFFERENT focus zone.

Action Plan 3:
A third action OR a monitoring recommendation if signals are weak.

--- HONESTY CLAUSE ---

If the data supports only surface-level insights,
do NOT inflate depth.
Clarity and honesty are preferred over sophistication.

"""

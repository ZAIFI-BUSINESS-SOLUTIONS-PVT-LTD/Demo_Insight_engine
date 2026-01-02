# Pace Analytics: Execution & Architecture Guidelines

**Status**: MVP‑FROZEN (Phases 0‑3 implemented)
**Last Updated**: 2025‑12‑22

## Current Status (MVP)

### Phase 0 – Case 0 (Ingestion & Normalization)
- **Objective**: Convert raw client uploads into a canonical `ResponseSheet.csv`.
- **Implemented**: Sheet extraction, online/offline transformers, validation, graceful skipping of classes missing `QuestionPaper.pdf`.
- **Accepted deviations**: No automatic download of missing PDFs, no retry logic, no longitudinal merging.

### Phase 1 – Case 1 (Ground‑Truth Extraction)
- **Objective**: Produce `questionpaper.json`, `solution.json`, `merged.json` and mechanical CSV analytics.
- **Implemented**: Gemini parsing of `QuestionPaper.pdf` and optional `Solutions.pdf`, deterministic merge, fail‑fast validation, mechanical student analytics (no LLM reasoning).
- **Accepted deviations**: When `Solutions.pdf` is absent, placeholder text is used; ground‑truth files are never altered after creation.

### Phase 2 – Case 2 (Student‑Level Reasoning)
- **Objective**: Create per‑student packets, invoke one LLM call per student, output `student_question_insights.csv` and `student_insight_summary.csv`.
- **Implemented**: Packetisation, single Gemini call per student, output validation, flagging of problematic rows (still written).
- **Accepted deviations**: No automatic retry of failed LLM calls, no batch processing, no multi‑turn reasoning.

### Phase 3 – Case 3 (Class‑Level Synthesis)
- **Objective**: One Gemini call per class to produce three focus zones and three action plans in `class_level_focus_and_action.csv`.
- **Implemented**: Strict single‑call, teacher‑level framing, verb‑check on action plans, privacy‑preserving output.
- **Accepted deviations**: No multi‑class aggregation, fixed number of focus zones/action plans, no UI rendering.

## Key Engineering Decisions & Guardrails

- **Phase 0** – Classes missing `QuestionPaper.pdf` are skipped; processing continues for remaining classes.
- **Phase 1** – `correct_option` is sourced **only** from `answer_key.json`; `Solutions.pdf` enriches `solution_text` and `key_concept` but never alters correctness. No LLM reasoning is performed.
- **Phase 2** – Ground‑truth files (`merged.json`, `ResponseSheet.csv`) are immutable; each student receives exactly one Gemini call; LLM output is validated against the schema and repaired if necessary; failures are logged and the row is flagged, not aborting the whole phase.
- **Phase 3** – Exactly one Gemini call per class; output must contain exactly three focus zones and three action plans; any verb that does not start with an imperative is rewritten; student‑level language is stripped to keep the output teacher‑centric.

## Pipeline Overview (As‑Is)

```
Case 0 → Case 1 → Case 2 → Case 3
```

- **Case 0** (Phase 0): Reads raw Excel/PDFs from `client_uploads/`, writes canonical `ResponseSheet.csv` to `input/<class>/`.
- **Case 1** (Phase 1): Parses PDFs, merges question and solution data, produces `merged.json` and three CSV analytics files under `output/<class>/phase1/`.
- **Case 2** (Phase 2): Builds per‑student packets, calls Gemini once per student, writes `student_question_insights.csv` and `student_insight_summary.csv` under `output/<class>/phase2/`.
- **Case 3** (Phase 3): Consumes Phase 2 summaries, calls Gemini once per class, writes `class_level_focus_and_action.csv` at the root of `output/`.

## What the Pipeline Guarantees (MVP)

- **Truth immutability** – Outputs of earlier phases are never mutated.
- **Deterministic mechanical analytics** – Phase 0 and Phase 1 CSVs are produced without LLM randomness.
- **Graceful handling of missing data** – Classes without a `QuestionPaper.pdf` are skipped; missing `Solutions.pdf` yields placeholder text but does not halt the run.
- **No silent corruption** – All validation failures are logged and cause the phase to abort, never producing partially corrupted artifacts.
- **Teacher‑usable outputs** – Final CSVs contain only aggregated, teacher‑focused information.

## What Is Intentionally Out of Scope (For Now)

- Longitudinal or cross‑class analysis.
- Automatic retry or back‑off logic for failed LLM calls.
- Advanced validation beyond schema checks (e.g., semantic consistency).
- Explainability tracing of LLM decisions.
- UI or web‑frontend integration.

## System Freeze Note

The pipeline (Case 0 – Case 3) is **MVP‑frozen** as of **2025‑12‑22**. Scope of the freeze includes:

- No changes to phase boundaries or data contracts.
- No addition of new LLM calls or modification of existing call patterns.
- No alteration of CSV schemas.

Any change that would modify the behaviour described above requires a formal design review and a new version release.

## Configuration Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Required** | Google Gemini API Key. |
| `TARGET_CLASS` | `class_medical` | Runs only for this class if set; blank runs all. |
| `MODEL_NAME` | `gemini-3.0-flash` | Gemini model version to use. |
| `RESPONSE_TYPE` | `BOTH` | `ONLINE`, `OFFLINE`, or `BOTH`. |

## Directory Map & Data Flow

```text
pace_analytics/
├── .env                        # Configuration variables
├── case0.py                    # Phase 0 Entry Point
├── case1.py                    # Phase 1 Entry Point
├── case2.py                    # Phase 2 Entry Point
├── case3.py                    # Phase 3 Entry Point
├── src/
│   ├── phase0/                 # Ingestion Logic
│   ├── phase1/                 # Extraction Logic
│   ├── phase2/                 # Student Analysis Logic
│   ├── phase3/                 # Class Synthesis Logic
│   └── prompts.py              # CENTRALIZED PROMPT REGISTRY
├── client_uploads/             # [DROP ZONE] User places raw files here
│   ├── responses/
│   │   └── Response_Online.xlsx
│   └── class_10 FB/
│       └── QuestionPaper.pdf
├── input/                      # [GENERATED SOURCE] Phase 0 writes valid files here
│   └── class_10 FB/
│       ├── ResponseSheet.csv
│       ├── answer_key.json
│       └── QuestionPaper.pdf
└── output/                     # [ARTIFACTS] System generation targets
    ├── class_level_focus_and_action.csv  # Phase 3 Final Output
    └── class_10 FB/
        ├── phase1/             # derived json truth
        │   ├── merged.json
        │   ├── questionpaper.json
        │   └── solution.json
        └── phase2/             # student insights
            ├── student_insight_summary.csv
            └── student_question_insights.csv
```

---

(End of updated PROJECT_INSTRUCTIONS.md)

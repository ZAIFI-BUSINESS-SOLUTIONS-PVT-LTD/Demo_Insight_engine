# Pace Analytics

This project automates the extraction and analysis of student exam data using LLMs.
It processes PDF question papers and solutions, and student response CSVs to generate insights and PDF reports.

## Folder Structure

- `input/`: Contains raw data (PDFs, CSVs) organized by class.
- `output/`: Stores processed JSON and CSV files, separated by phase.
- `src/`: Source code for the application.
  - `phase1/`: Data extraction and mechanical analytics.
  - `phase2/`: Qualitative analysis using LLMs.
  - `phase3/`: Class-level synthesis and action plans.
  - `phase4/`: Student data aggregation.
  - `phase5/`: Pattern insights generation.
  - `phase6/`: PDF report generation.
  - `utils/`: Shared utilities for file loading and validation.
- `phase1.md` / `phase2.md` / `phase6.md`: Documentation for LLM prompts and logic.

## How to Run

### Phase 1
Executes extraction and mechanical analytics.
```bash
python -m src.phase1.extract_questionpaper
python -m src.phase1.extract_solution
python -m src.phase1.merge_data
python -m src.phase1.generate_csvs
```

### Phase 2
Executes LLM-based reasoning and qualitative analysis.
```bash
python -m src.phase2.packetize_students
python -m src.phase2.llm_runner
python -m src.phase2.build_phase2_csvs
```

### Phase 3-5
Execute using case files:
```bash
python case3.py  # Class-level synthesis
python case4.py  # Student data aggregation
python case5.py  # Pattern insights
```

### Phase 6 (PDF Reports)
Generate PDF reports for students:
```bash
# All students
python case6.py

# Single student (set STUDENT_NAME in .env or environment)
$env:STUDENT_NAME="2025300001"; python case6.py
```

See [phase6.md](phase6.md) for detailed documentation.

**Note:** LLM prompts and logic are defined in phase1.md, phase2.md, and phase6.md.

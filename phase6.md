# Phase 6: PDF Report Generation

## Overview

Phase 6 generates comprehensive PDF reports for each student combining:
1. **Test-wise subject-wise performance charts** (from Phase 4 data)
2. **Pattern insights** (from Phase 5 analysis)

## Data Sources

### Phase 4 Data (`output/phase4/students/*.json`)
Contains per-student question records with:
- `correct_option`: The correct answer
- `student_selected_option`: Student's answer (empty string = unattempted)
- `test_name`: Test identifier
- `subject`: Subject name
- Other question metadata

### Phase 5 Data (`output/phase5/student_pattern_insights.json`)
Contains per-student insights (up to 5 per student) with:
- `insight_rank`: Priority (1-5)
- `topic`: Weak topic area
- `subject`: Subject
- `accuracy`: Performance percentage
- `problem`: Problem description
- `action`: Recommended action
- `citation`: Evidence from tests

## Scoring Logic

For each question, the answer is classified by comparing `correct_option` vs `student_selected_option`:

- **Correct**: `student_selected_option == correct_option` (and not empty) → **+4 marks**
- **Incorrect**: `student_selected_option != correct_option` (and not empty) → **-1 mark**
- **Unattempted**: `student_selected_option == ""` (empty string) → **0 marks**

Score formula: `Score = (Correct × 4) + (Incorrect × -1) + (Unattempted × 0)`

## Output Structure

```
output/
  phase6/
    charts/
      <student_id>_<test_name>.png    # Bar charts for each test
    reports/
      <student_id>_report.pdf         # Final PDF report
```

## Usage

### Generate Reports for All Students

```bash
python case6.py
```

### Generate Report for Specific Student

Set the `STUDENT_NAME` environment variable:

```bash
# Windows PowerShell
$env:STUDENT_NAME="2025300001"; python case6.py

# Or add to .env file
STUDENT_NAME=2025300001
```

Then run:
```bash
python case6.py
```

### Direct Module Usage

```python
from src.phase6.generate_reports import process

# All students
process()

# Single student
process(target_student_id="2025300001")
```

## Dependencies

Phase 6 requires additional Python packages:

```bash
pip install plotly kaleido reportlab
```

All dependencies are pure Python and work cross-platform without system libraries.

## Report Structure

Each PDF report contains:

### 1. Header
- Student ID
- Total questions attempted across all tests

### 2. Test-wise Performance Analysis
For each test:
- **Bar chart** showing subject-wise score breakdown
  - Green bars: Positive contribution from correct answers (+4 each)
  - Red bars: Negative contribution from incorrect answers (-1 each)
  - Total score annotation at top
- **Subject cards** with detailed metrics:
  - Correct count
  - Incorrect count
  - Unattempted count
  - Total questions
  - Net score

### 3. Learning Pattern Insights
For each insight (up to 5, ranked by priority):
- **Priority rank** (1-5)
- **Topic name** and subject
- **Accuracy percentage**
- **Problem identified**: What the student is struggling with
- **Recommended action**: Specific steps to improve
- **Evidence/Citation**: Which test questions support this insight

## Technical Flow

```
1. Load Phase 4 JSON (student records)
   ↓
2. Aggregate by test_name → subject
   ↓
3. For each record, classify answer:
      compare correct_option vs student_selected_option
   ↓
4. Calculate scores: correct×4 + incorrect×(-1) + unattempted×0
   ↓
5. Generate bar charts (Plotly → PNG via Kaleido)
   ↓
6. Load Phase 5 insights for student
   ↓
7. Build PDF using ReportLab (pure Python)
   - Add title and header
   - Insert charts as images
   - Add subject-wise tables
   - Format insights with priority highlighting
   ↓
8. Save to output/phase6/reports/
```

## Error Handling

- **Missing Phase 4 data**: Student is skipped with warning
- **Missing Phase 5 insights**: Report proceeds with empty insights section
- **Chart generation failure**: Error logged, student skipped
- **PDF conversion failure**: Error logged, student skipped

All errors are logged but do not halt processing of other students.

## Validation

After running Phase 6:

1. Check log output for errors
2. Verify PDF files in `output/phase6/reports/`
3. Open a sample PDF to verify:
   - All charts render correctly
   - Insights are properly formatted
   - Scores match expectations

## Limitations

- WeasyPrint requires system libraries (GTK/Cairo/Pango)
- Large test datasets may take time to render
- PDF file sizes vary based on number of tests and subjects

## Example Output

For student `2025300001` with 2 tests (class_7, class_8):

```
output/phase6/
  charts/
    2025300001_class_7.png
    2025300001_class_8.png
  reports/
    2025300001_report.pdf
    2025300001_report.html
```

The PDF will contain:
- 2 bar charts (one per test)
- Subject-wise breakdowns for each test
- 5 prioritized learning insights

## Integration with Existing Phases

Phase 6 is **read-only** and does not modify any existing phase outputs:
- Phase 0-3: No interaction
- Phase 4: Read-only access to `output/phase4/students/*.json`
- Phase 5: Read-only access to `output/phase5/student_pattern_insights.json`

Phase 6 can be run independently after Phase 4 and Phase 5 are complete.
